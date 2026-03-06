"""Dynamic execution tool for running converted Python files."""

from __future__ import annotations

import asyncio
import difflib
import os
import re
import sys
import time
from pathlib import Path
from typing import Any

from pydantic_ai import RunContext

from converter.context import ConversionContext

# ANSI colors for terminal output
_GREEN = "\033[92m"
_RED = "\033[91m"
_YELLOW = "\033[93m"
_CYAN = "\033[96m"
_DIM = "\033[2m"
_RESET = "\033[0m"

# Patterns for classifying expected (non-bug) errors in stderr
_EXPECTED_ERROR_PATTERNS: list[tuple[re.Pattern[str], str]] = [
    (re.compile(r"EOFError"), "EOFError: likely an unconverted uigetfile() — replace with glob-based auto-selection"),
    (re.compile(r"FileNotFoundError.*\.mat"), "Missing .mat data file — not a code bug"),
    (re.compile(r"ModuleNotFoundError"), "Optional module not installed — not a code bug"),
]


def _truncate_output(raw_bytes: bytes, max_bytes: int = 4096) -> str:
    """Decode raw bytes and truncate to max_bytes, keeping first+last half."""
    text = raw_bytes.decode("utf-8", errors="replace")
    if len(text) <= max_bytes:
        return text
    half = max_bytes // 2
    return text[:half] + f"\n\n... [{len(text) - max_bytes} chars truncated] ...\n\n" + text[-half:]


def _classify_expected_error(stderr: str, workspace_ready: bool = False) -> str | None:
    """Return a human-readable reason if stderr matches a known expected error, else None."""
    for pattern, reason in _EXPECTED_ERROR_PATTERNS:
        if pattern.search(stderr):
            # If workspace data was copied, .mat FileNotFoundError is a real bug
            if workspace_ready and "Missing .mat" in reason:
                continue
            return reason
    return None


def _log_execution_result(filename: str, result: dict[str, Any]) -> None:
    """Print execution results to the terminal so the user can follow along."""
    attempt = result.get("attempt", "?")
    elapsed = result.get("execution_time", 0.0)

    if result.get("max_attempts_reached"):
        print(f"  {_YELLOW}SKIP{_RESET} {filename} (max attempts reached)")
        return

    if result["success"]:
        print(f"  {_GREEN}PASS{_RESET} {filename} {_DIM}(attempt {attempt}, {elapsed}s){_RESET}")
    elif result.get("timed_out"):
        print(f"  {_YELLOW}TIMEOUT{_RESET} {filename} {_DIM}(attempt {attempt}, {elapsed}s){_RESET}")
    elif result.get("expected_error"):
        print(
            f"  {_YELLOW}EXPECTED{_RESET} {filename} — {result['expected_error']} "
            f"{_DIM}(attempt {attempt}){_RESET}"
        )
    else:
        print(f"  {_RED}FAIL{_RESET} {filename} {_DIM}(attempt {attempt}, rc={result['return_code']}, {elapsed}s){_RESET}")

    stdout = result.get("stdout", "").strip()
    stderr = result.get("stderr", "").strip()
    if stdout:
        for line in stdout.splitlines()[:10]:
            print(f"    {_DIM}stdout: {line}{_RESET}")
        if len(stdout.splitlines()) > 10:
            print(f"    {_DIM}... ({len(stdout.splitlines()) - 10} more lines){_RESET}")
    if stderr and not result["success"]:
        for line in stderr.splitlines()[:15]:
            print(f"    {_CYAN}stderr: {line}{_RESET}")
        if len(stderr.splitlines()) > 15:
            print(f"    {_DIM}... ({len(stderr.splitlines()) - 15} more lines){_RESET}")


async def execute_python_file(
    ctx: RunContext[ConversionContext],
    python_filename: str,
    timeout: int = 30,
) -> dict[str, Any]:
    """Run a converted Python file in a subprocess and return stdout/stderr.

    Use this after all static checks pass to catch runtime errors (bad imports,
    wrong array shapes, missing data files, etc.).

    Returns dict with success, return_code, stdout, stderr, timed_out,
    execution_time, attempt count, and optional expected_error classification.
    """
    python_filename = Path(python_filename).name
    file_path = ctx.deps.output_dir / python_filename

    # Track execution attempts
    attempt = ctx.deps.execution_attempts.get(python_filename, 0) + 1
    ctx.deps.execution_attempts[python_filename] = attempt

    max_attempts = ctx.deps.max_revision_attempts
    if attempt > max_attempts:
        result = {
            "success": False,
            "return_code": -1,
            "stdout": "",
            "stderr": (
                f"Max execution attempts reached ({max_attempts}) for '{python_filename}'. "
                "Stop retrying and proceed to the next file."
            ),
            "timed_out": False,
            "execution_time": 0.0,
            "attempt": attempt,
            "max_attempts_reached": True,
        }
        _log_execution_result(python_filename, result)
        return result

    # Check if file exists on disk; if only in cache, tell agent to write first
    if not file_path.exists():
        if python_filename in ctx.deps.converted_files:
            result = {
                "success": False,
                "return_code": -1,
                "stdout": "",
                "stderr": (
                    f"File '{python_filename}' is in the conversion cache but not on disk. "
                    "Call write_python_file first to flush it to disk before executing."
                ),
                "timed_out": False,
                "execution_time": 0.0,
                "attempt": attempt,
            }
            _log_execution_result(python_filename, result)
            return result
        result = {
            "success": False,
            "return_code": -1,
            "stdout": "",
            "stderr": f"File not found: {file_path}",
            "timed_out": False,
            "execution_time": 0.0,
            "attempt": attempt,
        }
        _log_execution_result(python_filename, result)
        return result

    # Build subprocess environment
    env = os.environ.copy()
    env["MPLBACKEND"] = "Agg"  # prevent matplotlib GUI windows

    # Prepend output_dir to PYTHONPATH so sibling scripts can import each other
    output_dir_str = str(ctx.deps.output_dir.resolve())
    existing_pythonpath = env.get("PYTHONPATH", "")
    env["PYTHONPATH"] = (
        f"{output_dir_str}{os.pathsep}{existing_pythonpath}"
        if existing_pythonpath
        else output_dir_str
    )

    timed_out = False
    start = time.monotonic()

    try:
        # Uses create_subprocess_exec (not shell=True) to avoid command injection
        process = await asyncio.create_subprocess_exec(
            sys.executable,
            str(file_path),
            stdin=asyncio.subprocess.DEVNULL,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
            cwd=str(ctx.deps.output_dir),
            env=env,
        )

        try:
            stdout_bytes, stderr_bytes = await asyncio.wait_for(
                process.communicate(), timeout=timeout
            )
        except asyncio.TimeoutError:
            process.kill()
            # Drain any remaining output
            stdout_bytes, stderr_bytes = await process.communicate()
            timed_out = True

    except OSError as exc:
        elapsed = time.monotonic() - start
        result = {
            "success": False,
            "return_code": -1,
            "stdout": "",
            "stderr": f"Failed to start subprocess: {exc}",
            "timed_out": False,
            "execution_time": round(elapsed, 3),
            "attempt": attempt,
        }
        _log_execution_result(python_filename, result)
        return result

    elapsed = time.monotonic() - start
    return_code = process.returncode if process.returncode is not None else -9
    stderr_text = _truncate_output(stderr_bytes)

    result: dict[str, Any] = {
        "success": return_code == 0 and not timed_out,
        "return_code": return_code,
        "stdout": _truncate_output(stdout_bytes),
        "stderr": stderr_text,
        "timed_out": timed_out,
        "execution_time": round(elapsed, 3),
        "attempt": attempt,
    }

    # Classify expected errors so the agent knows to move on
    if not result["success"] and not timed_out:
        expected = _classify_expected_error(stderr_text, workspace_ready=ctx.deps.workspace_ready)
        if expected:
            result["expected_error"] = expected

    # Auto-capture error lesson on success after previous failures
    if result["success"] and attempt > 1:
        history = ctx.deps.revision_history.get(python_filename, [])
        if len(history) >= 2:
            lesson = _generate_error_lesson(python_filename, history[0], history[-1], attempt)
            if lesson:
                ctx.deps.error_lessons.append(lesson)

    _log_execution_result(python_filename, result)
    return result


def _generate_error_lesson(
    filename: str, first_version: str, current_version: str, attempt: int
) -> str | None:
    """Generate a short error lesson by diffing the first and final code versions."""
    first_lines = first_version.splitlines(keepends=True)
    current_lines = current_version.splitlines(keepends=True)

    diff = list(difflib.unified_diff(first_lines, current_lines, n=0))
    if not diff:
        return None

    # Collect changed lines (skip diff headers)
    removed = []
    added = []
    for line in diff:
        if line.startswith("---") or line.startswith("+++") or line.startswith("@@"):
            continue
        if line.startswith("-"):
            removed.append(line[1:].strip())
        elif line.startswith("+"):
            added.append(line[1:].strip())

    # Filter out empty lines
    removed = [r for r in removed if r]
    added = [a for a in added if a]

    if not removed and not added:
        return None

    # Build a concise summary from the first few changes
    changes = []
    for r, a in zip(removed[:3], added[:3]):
        # Truncate long lines
        r_short = r[:60] + "..." if len(r) > 60 else r
        a_short = a[:60] + "..." if len(a) > 60 else a
        changes.append(f"'{r_short}' → '{a_short}'")

    extra_removed = len(removed) - min(len(removed), 3)
    extra_added = len(added) - min(len(added), 3)

    summary = f"{filename}: Fixed after {attempt} attempts. Key changes: " + "; ".join(changes)
    if extra_removed or extra_added:
        summary += f" (+{extra_removed + extra_added} more changes)"

    return summary
