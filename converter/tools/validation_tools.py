"""Validation tools for checking converted Python files."""

from __future__ import annotations

import ast
import re
from typing import Any

from pydantic_ai import RunContext

from converter.context import ConversionContext


async def validate_python_syntax(
    ctx: RunContext[ConversionContext],
    python_filename: str,
) -> dict[str, Any]:
    """Check if a Python file has valid syntax using compile().

    Returns dict with:
      - valid: bool
      - errors: list of error strings
      - error_context: code snippet around the error (if any)
    """
    content = ctx.deps.converted_files.get(python_filename, "")
    if not content:
        # Try reading from disk
        path = ctx.deps.output_dir / python_filename
        if not path.exists():
            return {"valid": False, "errors": [f"File not found: {python_filename}"], "error_context": ""}
        content = path.read_text(encoding="utf-8")

    try:
        compile(content, python_filename, "exec")
        return {"valid": True, "errors": [], "error_context": ""}
    except SyntaxError as e:
        error_msg = f"SyntaxError at line {e.lineno}: {e.msg}"
        context = _get_error_context(content, e.lineno or 0)
        # Store error in context
        if python_filename not in ctx.deps.conversion_errors:
            ctx.deps.conversion_errors[python_filename] = []
        ctx.deps.conversion_errors[python_filename].append(error_msg)
        return {
            "valid": False,
            "errors": [error_msg],
            "error_context": context,
        }
    except Exception as e:
        return {"valid": False, "errors": [str(e)], "error_context": ""}


async def run_pyflakes(
    ctx: RunContext[ConversionContext],
    python_filename: str,
) -> dict[str, Any]:
    """Run pyflakes on a converted file to find undefined names and unused imports.

    Returns dict with:
      - clean: bool (True if no issues)
      - undefined_names: list of undefined name warnings
      - unused_imports: list of unused import warnings
      - other_warnings: list of other warnings
      - raw_output: full pyflakes output
    """
    try:
        from pyflakes import api as pyflakes_api
        from pyflakes.checker import Checker
        import pyflakes.messages as pyflakes_messages
        import io
    except ImportError:
        return {
            "clean": False,
            "undefined_names": [],
            "unused_imports": [],
            "other_warnings": ["pyflakes not installed"],
            "raw_output": "pyflakes not available",
        }

    content = ctx.deps.converted_files.get(python_filename, "")
    if not content:
        path = ctx.deps.output_dir / python_filename
        if path.exists():
            content = path.read_text(encoding="utf-8")
        else:
            return {
                "clean": False,
                "undefined_names": [],
                "unused_imports": [],
                "other_warnings": [f"File not found: {python_filename}"],
                "raw_output": "",
            }

    # Run pyflakes via its API
    warning_count = pyflakes_api.check(content, python_filename)

    # Parse output by running through checker directly
    try:
        tree = compile(content, python_filename, "exec", ast.PyCF_ONLY_AST)
        checker = Checker(tree, filename=python_filename)
        messages = checker.messages
    except SyntaxError as e:
        return {
            "clean": False,
            "undefined_names": [],
            "unused_imports": [],
            "other_warnings": [f"SyntaxError: {e}"],
            "raw_output": f"SyntaxError: {e}",
        }

    undefined_names = []
    unused_imports = []
    other_warnings = []

    for msg in messages:
        msg_str = str(msg)
        if "undefined name" in msg_str or "UndefinedName" in type(msg).__name__:
            undefined_names.append(msg_str)
        elif "imported but unused" in msg_str or "UnusedImport" in type(msg).__name__:
            unused_imports.append(msg_str)
        else:
            other_warnings.append(msg_str)

    return {
        "clean": len(messages) == 0,
        "undefined_names": undefined_names,
        "unused_imports": unused_imports,
        "other_warnings": other_warnings,
        "raw_output": "\n".join(str(m) for m in messages),
        "total_warnings": len(messages),
    }


async def check_numpy_indexing(
    ctx: RunContext[ConversionContext],
    python_filename: str,
) -> dict[str, Any]:
    """Heuristic check for common 1-based indexing mistakes.

    Flags:
      - range_1_n: loops starting with range(1, n) where variable used as array index
      - column_1_access: [:, 1] or [1, :] patterns (likely should be 0)
      - find_no_index: np.where() result used without [0]
      - arithmetic_index_suspicious: arithmetic expressions in index that may need -1
    """
    content = ctx.deps.converted_files.get(python_filename, "")
    if not content:
        path = ctx.deps.output_dir / python_filename
        if path.exists():
            content = path.read_text(encoding="utf-8")
        else:
            return {"error": f"File not found: {python_filename}"}

    lines = content.splitlines()
    flags = {
        "range_1_n_with_index": [],
        "column_1_access": [],
        "find_no_index": [],
        "arithmetic_index_suspicious": [],
        "summary": "",
    }

    # Pattern: range(1, ...) — loop var might be used as array index without -1
    range_1_pattern = re.compile(r"\bfor\s+(\w+)\s+in\s+range\s*\(\s*1\s*,")
    # Array index using the loop var directly: var[loop_var] or [:, loop_var]
    # (suspicious when loop var comes from range(1,...))
    range_vars: dict[int, str] = {}  # line_num → var_name
    for i, line in enumerate(lines, 1):
        m = range_1_pattern.search(line)
        if m:
            range_vars[i] = m.group(1)

    # Check if those vars are used as direct array indices
    for start_line, var in range_vars.items():
        # Look ahead for uses of this variable in array indexing
        index_pattern = re.compile(
            rf"\[\s*{re.escape(var)}\s*\]|\[.*,\s*{re.escape(var)}\s*\]|"
            rf"\[\s*{re.escape(var)}\s*,",
        )
        for i, line in enumerate(lines[start_line:], start_line + 1):
            if re.search(r"\bfor\b", line) and var in line:
                break  # End of loop scope approximation
            if index_pattern.search(line):
                flags["range_1_n_with_index"].append(
                    f"Line {i}: loop var '{var}' from range(1,...) used directly as index — verify offset: {line.strip()}"
                )

    # Pattern: [:, 1] or [1, :] — potential off-by-one (should be index 0?)
    col_1_pattern = re.compile(r"\[:,\s*1\s*\]|\[\s*1\s*,\s*:\s*\]|\[\s*1\s*\]")
    for i, line in enumerate(lines, 1):
        if col_1_pattern.search(line) and not line.strip().startswith("#"):
            flags["column_1_access"].append(
                f"Line {i}: index 1 found — verify this is intentional (0-based): {line.strip()}"
            )

    # Pattern: np.where(...) without [0] — returns tuple of arrays
    where_pattern = re.compile(r"np\.where\s*\([^)]+\)(?!\s*\[)")
    for i, line in enumerate(lines, 1):
        if where_pattern.search(line) and "=" in line and not line.strip().startswith("#"):
            flags["find_no_index"].append(
                f"Line {i}: np.where() result may need [0] to get indices: {line.strip()}"
            )

    # Pattern: arithmetic in index without obvious -1 offset
    # e.g., [2*k] or [3*i] where k/i likely comes from a 1-based loop
    arith_index = re.compile(r"\[\s*\d+\s*\*\s*\w+\s*\]|\[\s*\w+\s*\*\s*\d+\s*\]")
    for i, line in enumerate(lines, 1):
        if arith_index.search(line) and not line.strip().startswith("#"):
            # Check if there's no -1 or -2 following
            if not re.search(r"\d+\s*\*\s*\w+\s*-\s*\d", line) and not re.search(r"\w+\s*\*\s*\d+\s*-\s*\d", line):
                flags["arithmetic_index_suspicious"].append(
                    f"Line {i}: arithmetic index without offset — verify 1-based conversion: {line.strip()}"
                )

    total_flags = sum(len(v) for v in flags.values() if isinstance(v, list))
    flags["summary"] = f"{total_flags} potential indexing issues found"

    return flags


async def validate_imports(
    ctx: RunContext[ConversionContext],
    python_filename: str,
) -> dict[str, Any]:
    """AST-parse the file to verify all name uses have matching imports.

    Returns:
      - ok: bool
      - missing_imports: list of names used but not imported/defined
      - unused_imports: list of imports never used
    """
    content = ctx.deps.converted_files.get(python_filename, "")
    if not content:
        path = ctx.deps.output_dir / python_filename
        if path.exists():
            content = path.read_text(encoding="utf-8")
        else:
            return {"ok": False, "missing_imports": [], "unused_imports": [], "error": "File not found"}

    try:
        tree = ast.parse(content, filename=python_filename)
    except SyntaxError as e:
        return {"ok": False, "missing_imports": [], "unused_imports": [], "error": f"SyntaxError: {e}"}

    # Collect all names defined at module level
    defined_names: set[str] = set()
    imported_names: set[str] = set()
    used_names: set[str] = set()

    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                name = alias.asname or alias.name.split(".")[0]
                imported_names.add(name)
                defined_names.add(name)
        elif isinstance(node, ast.ImportFrom):
            for alias in node.names:
                name = alias.asname or alias.name
                if name != "*":
                    imported_names.add(name)
                    defined_names.add(name)
        elif isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            defined_names.add(node.name)
        elif isinstance(node, ast.Assign):
            for target in node.targets:
                if isinstance(target, ast.Name):
                    defined_names.add(target.id)
        elif isinstance(node, ast.Name) and isinstance(node.ctx, ast.Load):
            used_names.add(node.id)

    # Common builtins and special names that don't need imports
    builtins = {
        "print", "len", "range", "int", "float", "str", "bool", "list", "dict",
        "set", "tuple", "type", "isinstance", "issubclass", "hasattr", "getattr",
        "setattr", "delattr", "callable", "iter", "next", "enumerate", "zip",
        "map", "filter", "sorted", "reversed", "min", "max", "sum", "abs",
        "round", "pow", "divmod", "chr", "ord", "hex", "oct", "bin", "format",
        "repr", "vars", "dir", "id", "hash", "open", "input", "super",
        "staticmethod", "classmethod", "property", "object", "Exception",
        "ValueError", "TypeError", "KeyError", "IndexError", "AttributeError",
        "NotImplementedError", "RuntimeError", "OSError", "IOError",
        "True", "False", "None", "__name__", "__file__", "__doc__",
        "ArithmeticError", "ImportError", "StopIteration",
    }

    potentially_missing = (used_names - defined_names - builtins)

    return {
        "ok": len(potentially_missing) == 0,
        "potentially_missing": sorted(potentially_missing),
        "imported_names": sorted(imported_names),
        "defined_at_module_level": sorted(defined_names - imported_names),
    }


async def annotate_error_in_source(
    ctx: RunContext[ConversionContext],
    python_filename: str,
    error_message: str,
) -> str:
    """Return source lines around the error location for targeted revision.

    Extracts line number from error_message (if present) and returns ±5 lines
    of context with line numbers for easy identification. Tracks repeated errors
    and provides pattern-specific hints.
    """
    content = ctx.deps.converted_files.get(python_filename, "")
    if not content:
        path = ctx.deps.output_dir / python_filename
        if path.exists():
            content = path.read_text(encoding="utf-8")
        else:
            return f"Cannot annotate: file not found ({python_filename})"

    lines = content.splitlines()
    total_lines = len(lines)

    # Track this annotation for repeat detection
    key = python_filename
    if key not in ctx.deps.error_annotations:
        ctx.deps.error_annotations[key] = []
    ctx.deps.error_annotations[key].append(error_message)

    # Count previous occurrences of the same error class
    repeat_count = sum(
        1 for prev in ctx.deps.error_annotations[key][:-1]
        if _same_error_class(prev, error_message)
    )

    # Try to extract line number from error message
    line_num_match = re.search(r"line\s+(\d+)", error_message, re.IGNORECASE)
    if not line_num_match:
        # Return first 20 lines as fallback
        snippet = "\n".join(f"{i+1:4}: {l}" for i, l in enumerate(lines[:20]))
        result = f"Error: {error_message}\n\n(Could not determine line number; showing first 20 lines)\n{snippet}"
    else:
        error_line = int(line_num_match.group(1))
        context_start = max(0, error_line - 6)
        context_end = min(total_lines, error_line + 5)

        snippet_lines = []
        for i in range(context_start, context_end):
            marker = ">>> " if i + 1 == error_line else "    "
            snippet_lines.append(f"{marker}{i+1:4}: {lines[i]}")

        result = (
            f"Error: {error_message}\n"
            f"File: {python_filename}\n"
            f"Context (lines {context_start+1}–{context_end}):\n"
            + "\n".join(snippet_lines)
        )
        error_line_for_hint = error_line
    # For hint lookup, use extracted line or None
    error_line_for_hint = int(line_num_match.group(1)) if line_num_match else None

    # Append repeat warning if applicable
    if repeat_count > 0:
        result += (
            f"\n\n⚠ REPEATED ERROR (seen {repeat_count + 1} times for this file). "
            "Your previous rewrite(s) did NOT fix this. "
            "Try a fundamentally different approach: extract complex expressions "
            "to variables, use different string quoting, or restructure the logic."
        )

    # Append pattern-specific hints
    hint = _get_error_hint(error_message, content, error_line_for_hint)
    if hint:
        result += f"\n\n💡 HINT: {hint}"

    # Include lessons from other files if available
    if ctx.deps.error_lessons:
        result += "\n\n📝 Lessons from earlier files:\n" + "\n".join(
            f"  - {lesson}" for lesson in ctx.deps.error_lessons
        )

    return result


def _same_error_class(a: str, b: str) -> bool:
    """Check if two error messages are the same class (same exception type)."""
    # Extract the exception type (e.g. "TypeError", "IndexError")
    pattern = re.compile(r"((?:[A-Z]\w*)?Error|Exception)")
    types_a = pattern.findall(a)
    types_b = pattern.findall(b)
    if not types_a or not types_b:
        return False
    return types_a[0] == types_b[0]


# Common error patterns: (error_regex, code_regex_or_None, hint_text)
_ERROR_HINTS: list[tuple[re.Pattern[str], re.Pattern[str] | None, str]] = [
    (
        re.compile(r"TypeError.*tuple indices must be integers.*not str", re.IGNORECASE),
        re.compile(r"""f['"].*\[['"]"""),
        "This is likely an f-string quoting conflict. `f'...{d[\"key\"]}'` breaks when "
        "outer and inner quotes clash. Fix: extract the dict lookup to a variable before "
        "the f-string, e.g. `val = d['key']; print(f'... {val}')`, or use different quotes.",
    ),
    (
        re.compile(r"IndexError.*index.*out of", re.IGNORECASE),
        None,
        "Likely a 1-based to 0-based indexing error. MATLAB is 1-based, Python is 0-based. "
        "Check loop ranges and array indices — subtract 1 from MATLAB indices.",
    ),
    (
        re.compile(r"NameError.*name '(\w+)' is not defined", re.IGNORECASE),
        None,
        "Check if this name was supposed to be imported or defined earlier in the file. "
        "Common causes: missing import, variable defined inside a function but used outside, "
        "or a MATLAB built-in that needs a Python equivalent.",
    ),
    (
        re.compile(r"KeyError", re.IGNORECASE),
        None,
        "Verify the dict key exists. For scipy.io.loadmat, use mat_to_dict() and check "
        "actual key names — loadmat adds '__header__', '__version__', '__globals__' keys "
        "and may nest data differently than expected.",
    ),
    (
        re.compile(r"TypeError.*not str", re.IGNORECASE),
        re.compile(r"""f['"]"""),
        "Possible f-string quoting conflict. When using dict access inside f-strings, "
        "extract the value to a variable first: `val = d['key']; f'...{val}...'`.",
    ),
]


def _get_error_hint(error_message: str, content: str, error_line: int | None) -> str | None:
    """Check error+code patterns and return the first matching hint, or None."""
    # Get the error line content if available
    lines = content.splitlines()
    line_content = ""
    if error_line and 0 < error_line <= len(lines):
        # Check a few lines around the error for context
        start = max(0, error_line - 3)
        end = min(len(lines), error_line + 2)
        line_content = "\n".join(lines[start:end])

    for error_pattern, code_pattern, hint in _ERROR_HINTS:
        if error_pattern.search(error_message):
            if code_pattern is None:
                return hint
            # Check if code pattern matches in the nearby lines
            if line_content and code_pattern.search(line_content):
                return hint
            # Also check the full content as fallback
            if code_pattern.search(content):
                return hint
    return None


def _get_error_context(content: str, error_line: int, context: int = 5) -> str:
    """Get lines around an error for display."""
    lines = content.splitlines()
    start = max(0, error_line - context - 1)
    end = min(len(lines), error_line + context)
    result = []
    for i in range(start, end):
        marker = ">>> " if i + 1 == error_line else "    "
        result.append(f"{marker}{i+1:4}: {lines[i]}")
    return "\n".join(result)
