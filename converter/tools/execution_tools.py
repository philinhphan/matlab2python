"""Dynamic execution tool for running converted Python files."""

from __future__ import annotations

import asyncio
import os
import re
import sys
import time
from pathlib import Path
from typing import Any

from pydantic_ai import RunContext

from converter.context import ConversionContext

# Patterns for classifying expected (non-bug) errors in stderr
_EXPECTED_ERROR_PATTERNS: list[tuple[re.Pattern[str], str]] = [
    (re.compile(r"EOFError"), "EOFError from input() stub — not a code bug"),
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


def _classify_expected_error(stderr: str) -> str | None:
    """Return a human-readable reason if stderr matches a known expected error, else None."""
    for pattern, reason in _EXPECTED_ERROR_PATTERNS:
        if pattern.search(stderr):
            return reason
    return None


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
        return {
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

    # Check if file exists on disk; if only in cache, tell agent to write first
    if not file_path.exists():
        if python_filename in ctx.deps.converted_files:
            return {
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
        return {
            "success": False,
            "return_code": -1,
            "stdout": "",
            "stderr": f"File not found: {file_path}",
            "timed_out": False,
            "execution_time": 0.0,
            "attempt": attempt,
        }

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
            cwd=str(ctx.deps.input_dir),
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
        return {
            "success": False,
            "return_code": -1,
            "stdout": "",
            "stderr": f"Failed to start subprocess: {exc}",
            "timed_out": False,
            "execution_time": round(elapsed, 3),
            "attempt": attempt,
        }

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
        expected = _classify_expected_error(stderr_text)
        if expected:
            result["expected_error"] = expected

    return result
