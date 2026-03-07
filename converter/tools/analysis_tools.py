"""Analysis tools for scanning MATLAB source code patterns and data files."""

from __future__ import annotations

import os
import re
from pathlib import Path
from typing import Any

import numpy as np
import scipy.io

from pydantic_ai import RunContext

from converter.context import ConversionContext


# Patterns for detecting MATLAB features
_FUNCTION_DEF_RE = re.compile(
    r"^\s*function\s+(?:(\[[^\]]*\]|\w+)\s*=\s*)?(\w+)\s*\(([^)]*)\)",
    re.MULTILINE,
)
_DYNAMIC_STRUCT_RE = re.compile(r"\w+\.\([^)]+\)")
_GUI_CALLS_RE = re.compile(
    r"\b(uigetfile|uiputfile|uigetdir|msgbox|inputdlg|questdlg|errordlg|warndlg|"
    r"waitbar|guidata|guihandles|openfig|uicontrol|figure|uimenu)\b"
)
_EVAL_SPRINTF_RE = re.compile(r"\beval\s*\(|\bsprintf\s*\(")
_MAT_LOAD_RE = re.compile(r"\bload\s*\(|\bsave\s*\(")
_POLAR_PLOT_RE = re.compile(r"\bpolar\s*\(")
_SUBTIGHTPLOT_RE = re.compile(r"\bsubtightplot\s*\(")
_INTERP1_RE = re.compile(r"\binterp1\s*\(")
_ASSIGNIN_RE = re.compile(r"\bassignin\s*\(")
_ADDPATH_RE = re.compile(r"\baddpath\s*\(")
_PYENV_RE = re.compile(r"\bpyenv\b|\bpyrunfile\b|\bpy\.\w+")
_CELL_ARRAY_RE = re.compile(r"\{|\}")
_1BASED_ARITHMETIC_RE = re.compile(
    r"\(\s*\w+\s*\*\s*\w+\s*(?:[+-]\s*\d+)?\s*\)",  # e.g. (2*kk) or (2*kk-1)
)
_COMMENT_RE = re.compile(r"%.*$", re.MULTILINE)
_FUNCTION_CALL_RE = re.compile(r"\b([a-zA-Z_]\w*)\s*\(")


def _strip_comments(source: str) -> str:
    """Remove MATLAB line comments for cleaner pattern matching."""
    return _COMMENT_RE.sub("", source)


async def analyze_matlab_patterns(
    ctx: RunContext[ConversionContext],
    filename: str,
) -> dict[str, Any]:
    """Scan a MATLAB file and return a dict of detected patterns.

    Returns flags indicating which conversion strategies are needed.
    """
    source = ctx.deps.matlab_sources.get(filename, "")
    if not source:
        return {"error": f"File {filename} not loaded; call read_matlab_file first"}

    clean = _strip_comments(source)

    # Detect function definitions
    function_defs = []
    for m in _FUNCTION_DEF_RE.finditer(source):
        returns_raw = m.group(1) or ""
        name = m.group(2)
        args_raw = m.group(3) or ""
        # Parse return values
        returns = [r.strip() for r in returns_raw.strip("[]").split(",") if r.strip()]
        args = [a.strip() for a in args_raw.split(",") if a.strip()]
        function_defs.append({"name": name, "args": args, "returns": returns})

    # Detect called functions (excluding MATLAB builtins and keywords)
    matlab_keywords = {
        "if", "else", "elseif", "end", "for", "while", "switch", "case",
        "otherwise", "try", "catch", "break", "continue", "return", "function",
        "classdef", "properties", "methods", "events", "enumeration",
    }
    called_functions = set()
    for m in _FUNCTION_CALL_RE.finditer(clean):
        name = m.group(1)
        if name not in matlab_keywords:
            called_functions.add(name)

    # Detect eval(sprintf()) specifically — the most dangerous pattern
    has_eval_sprintf = bool(_EVAL_SPRINTF_RE.search(clean))

    # Check for arithmetic index patterns like (2*kk) or (3*i-1)
    has_arithmetic_index = bool(_1BASED_ARITHMETIC_RE.search(clean))

    # Count load/save calls
    mat_io_matches = _MAT_LOAD_RE.findall(clean)

    return {
        "filename": filename,
        "has_dynamic_struct_access": bool(_DYNAMIC_STRUCT_RE.search(clean)),
        "has_gui_calls": bool(_GUI_CALLS_RE.search(clean)),
        "has_eval_sprintf": has_eval_sprintf,
        "has_mat_load": bool(_MAT_LOAD_RE.search(clean)),
        "mat_io_call_count": len(mat_io_matches),
        "has_polar_plot": bool(_POLAR_PLOT_RE.search(clean)),
        "has_subtightplot": bool(_SUBTIGHTPLOT_RE.search(clean)),
        "has_interp1": bool(_INTERP1_RE.search(clean)),
        "has_assignin": bool(_ASSIGNIN_RE.search(clean)),
        "has_pyenv_pyrunfile": bool(_PYENV_RE.search(clean)),
        "has_cell_arrays": bool(_CELL_ARRAY_RE.search(clean)),
        "has_arithmetic_index": has_arithmetic_index,
        "function_definitions": function_defs,
        "called_functions": sorted(called_functions),
        "line_count": len(source.splitlines()),
        "has_addpath": bool(_ADDPATH_RE.search(clean)),
        "has_german_comments": bool(
            re.search(r"[äöüÄÖÜß]", source)
        ),
    }


async def extract_function_signatures(
    ctx: RunContext[ConversionContext],
    filename: str,
) -> dict[str, dict]:
    """Extract all function signatures from a MATLAB file.

    Stores results in ctx.deps.known_functions and returns them.
    Returns dict mapping function_name → {args, returns, file}.
    """
    source = ctx.deps.matlab_sources.get(filename, "")
    if not source:
        return {}

    extracted: dict[str, dict] = {}
    for m in _FUNCTION_DEF_RE.finditer(source):
        returns_raw = m.group(1) or ""
        name = m.group(2)
        args_raw = m.group(3) or ""
        returns = [r.strip() for r in returns_raw.strip("[]").split(",") if r.strip()]
        args = [a.strip() for a in args_raw.split(",") if a.strip()]
        info = {"args": args, "returns": returns, "file": filename}
        extracted[name] = info
        ctx.deps.known_functions[name] = info

    return extracted


async def build_dependency_graph(
    ctx: RunContext[ConversionContext],
) -> dict[str, Any]:
    """Build a dependency graph across all loaded MATLAB files.

    Cross-references function calls to determine which files define functions
    called by other files. Returns both the graph and a suggested conversion order.
    """
    # Make sure all files are analyzed
    all_files = list(ctx.deps.matlab_sources.keys())

    # Map: function_name → defining_filename
    fn_to_file: dict[str, str] = {}
    for fn_name, fn_info in ctx.deps.known_functions.items():
        fn_to_file[fn_name] = fn_info.get("file", "unknown")

    # Build graph: file → list of files it depends on
    graph: dict[str, list[str]] = {}
    for filename in all_files:
        source = ctx.deps.matlab_sources[filename]
        clean = _strip_comments(source)
        deps = set()
        for m in _FUNCTION_CALL_RE.finditer(clean):
            called = m.group(1)
            if called in fn_to_file and fn_to_file[called] != filename:
                deps.add(fn_to_file[called])
        graph[filename] = sorted(deps)

    ctx.deps.dependency_graph = graph

    # Topological sort for conversion order
    order = _topological_sort(graph)

    return {
        "dependency_graph": graph,
        "suggested_conversion_order": order,
        "total_files": len(all_files),
    }


def _topological_sort(graph: dict[str, list[str]]) -> list[str]:
    """Return files in topological order (dependencies first)."""
    visited: set[str] = set()
    result: list[str] = []

    def visit(node: str) -> None:
        if node in visited:
            return
        visited.add(node)
        for dep in graph.get(node, []):
            visit(dep)
        result.append(node)

    for node in graph:
        visit(node)

    return result


def _describe_value(val: Any, max_elements: int = 20) -> str:
    """Produce a human-readable description of a numpy value from a .mat file."""
    if not isinstance(val, np.ndarray):
        return f"  type={type(val).__name__}, value={val!r}"

    lines: list[str] = []

    # Structured array (MATLAB struct)
    if val.dtype.names is not None:
        lines.append(f"  MATLAB struct, shape={val.shape}, fields:")
        squeezed = val.squeeze()
        if squeezed.ndim == 0:
            s = squeezed[()]
            for name in val.dtype.names:
                field_val = s[name]
                if isinstance(field_val, np.ndarray):
                    if field_val.dtype.names:
                        lines.append(f"    {name}: nested struct, fields={field_val.dtype.names}")
                    elif field_val.dtype == object:
                        lines.append(f"    {name}: cell array, shape={field_val.shape}")
                    elif field_val.dtype.kind in ('U', 'S'):
                        lines.append(f"    {name}: string = {str(field_val.squeeze())!r}")
                    elif field_val.size <= max_elements:
                        lines.append(f"    {name}: shape={field_val.shape}, dtype={field_val.dtype}, values={field_val.squeeze()!r}")
                    else:
                        lines.append(f"    {name}: shape={field_val.shape}, dtype={field_val.dtype}")
                else:
                    lines.append(f"    {name}: {field_val!r}")
        return "\n".join(lines)

    # Object array (MATLAB cell)
    if val.dtype == object:
        lines.append(f"  cell array, shape={val.shape}")
        for i, elem in enumerate(val.flat):
            if i >= 10:
                lines.append(f"    ... ({val.size - 10} more elements)")
                break
            if isinstance(elem, np.ndarray):
                if elem.dtype.kind in ('U', 'S'):
                    lines.append(f"    [{i}]: string = {str(elem.squeeze())!r}")
                elif elem.size <= max_elements:
                    lines.append(f"    [{i}]: shape={elem.shape}, dtype={elem.dtype}, values={elem.squeeze()!r}")
                else:
                    lines.append(f"    [{i}]: shape={elem.shape}, dtype={elem.dtype}")
            else:
                lines.append(f"    [{i}]: {elem!r}")
        return "\n".join(lines)

    # String array
    if val.dtype.kind in ('U', 'S'):
        return f"  string, value={str(val.squeeze())!r}"

    # Numeric array
    if val.size <= max_elements:
        return f"  shape={val.shape}, dtype={val.dtype}, values={val.squeeze()!r}"
    return f"  shape={val.shape}, dtype={val.dtype}"


async def inspect_mat_file(
    ctx: RunContext[ConversionContext],
    file_path: str,
) -> str:
    """Load a .mat file and return a structured overview of its contents.

    Shows variable names, shapes, types, struct fields, and small values.
    Looks in output_dir first (workspace-copied), then input_dir as fallback.
    """
    # Resolve file path: try output_dir first, then input_dir
    candidates = [
        ctx.deps.output_dir / file_path,
        ctx.deps.input_dir / file_path,
    ]
    # Also search recursively if just a filename was given
    if "/" not in file_path and "\\" not in file_path:
        for search_dir in [ctx.deps.output_dir, ctx.deps.input_dir]:
            for root, _dirs, files in os.walk(search_dir):
                if file_path in files:
                    candidates.append(Path(root) / file_path)

    resolved = None
    for c in candidates:
        if c.is_file():
            resolved = c
            break

    if resolved is None:
        return f"ERROR: Could not find '{file_path}' in output or input directory."

    try:
        mat = scipy.io.loadmat(str(resolved), squeeze_me=False)
    except Exception as e:
        return f"ERROR loading '{resolved}': {e}"

    lines = [f"=== {file_path} (from {resolved.relative_to(ctx.deps.input_dir.parent)}) ==="]
    lines.append(f"Total variables: {sum(1 for k in mat if not k.startswith('__'))}")
    lines.append("")

    for key in sorted(mat.keys()):
        if key.startswith("__"):
            continue
        val = mat[key]
        lines.append(f"{key}:")
        lines.append(_describe_value(val))
        lines.append("")

    return "\n".join(lines)


async def list_mat_files(
    ctx: RunContext[ConversionContext],
    directory: str = "",
) -> str:
    """List all .mat files in the output directory (or a subdirectory), with sizes.

    Helps the agent discover what data files are available for inspection.
    """
    search_dir = ctx.deps.output_dir / directory if directory else ctx.deps.output_dir
    if not search_dir.is_dir():
        # Fallback to input dir
        search_dir = ctx.deps.input_dir / directory if directory else ctx.deps.input_dir

    if not search_dir.is_dir():
        return f"ERROR: Directory '{directory}' not found."

    mat_files: list[str] = []
    for root, _dirs, files in os.walk(search_dir):
        for f in sorted(files):
            if f.lower().endswith(".mat"):
                full = Path(root) / f
                rel = full.relative_to(search_dir)
                size_kb = full.stat().st_size / 1024
                mat_files.append(f"  {rel}  ({size_kb:.1f} KB)")

    if not mat_files:
        return f"No .mat files found in '{search_dir}'."

    header = f"=== .mat files in {search_dir.name}/{directory} ==="
    return header + "\n" + "\n".join(mat_files) + f"\n\nTotal: {len(mat_files)} files"
