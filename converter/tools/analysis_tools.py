"""Analysis tools for scanning MATLAB source code patterns."""

from __future__ import annotations

import re
from typing import Any

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
