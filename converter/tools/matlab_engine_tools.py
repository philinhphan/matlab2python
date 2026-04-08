"""MATLAB Engine tool for running original .m files (requires MATLAB license)."""

from __future__ import annotations

import asyncio
import io
import time
from pathlib import Path
from typing import Any

from pydantic_ai import RunContext

from converter.context import ConversionContext

# ANSI colors (match execution_tools.py)
_GREEN = "\033[92m"
_RED = "\033[91m"
_YELLOW = "\033[93m"
_DIM = "\033[2m"
_RESET = "\033[0m"

# Lazy singleton — started on first call, reused thereafter
_engine: Any = None


def _get_engine() -> Any:
    """Start or return the cached MATLAB engine instance."""
    global _engine
    if _engine is not None:
        return _engine

    import matlab.engine  # type: ignore[import-untyped]

    print(f"  {_DIM}Starting MATLAB engine (this may take ~10s)...{_RESET}")
    _engine = matlab.engine.start_matlab()
    return _engine


def _truncate(text: str, max_chars: int = 4096) -> str:
    if len(text) <= max_chars:
        return text
    half = max_chars // 2
    return text[:half] + f"\n\n... [{len(text) - max_chars} chars truncated] ...\n\n" + text[-half:]


def _run_matlab_script(input_dir: Path, filename: str, timeout: int) -> dict[str, Any]:
    """Synchronous helper — called via asyncio.to_thread."""
    import matlab.engine  # type: ignore[import-untyped]

    out = io.StringIO()
    err = io.StringIO()
    start = time.monotonic()
    script_name = Path(filename).stem  # MATLAB runs scripts by name, not path

    try:
        eng = _get_engine()
        eng.cd(str(input_dir), nargout=0)

        # Run the script with captured output streams
        eng.run(script_name, nargout=0, stdout=out, stderr=err)

        elapsed = time.monotonic() - start
        return {
            "success": True,
            "stdout": out.getvalue(),
            "stderr": err.getvalue(),
            "execution_time": round(elapsed, 3),
        }
    except matlab.engine.MatlabExecutionError as exc:
        elapsed = time.monotonic() - start
        return {
            "success": False,
            "stdout": out.getvalue(),
            "stderr": err.getvalue() or str(exc),
            "execution_time": round(elapsed, 3),
        }
    except Exception as exc:
        elapsed = time.monotonic() - start
        return {
            "success": False,
            "stdout": out.getvalue(),
            "stderr": f"Engine error: {exc}",
            "execution_time": round(elapsed, 3),
        }


def _log_result(filename: str, result: dict[str, Any]) -> None:
    elapsed = result["execution_time"]
    if result["success"]:
        print(f"  {_GREEN}MATLAB PASS{_RESET} {filename} {_DIM}({elapsed}s){_RESET}")
    else:
        print(f"  {_RED}MATLAB FAIL{_RESET} {filename} {_DIM}({elapsed}s){_RESET}")

    stdout = result.get("stdout", "").strip()
    stderr = result.get("stderr", "").strip()
    if stdout:
        for line in stdout.splitlines()[:10]:
            print(f"    {_DIM}stdout: {line}{_RESET}")
        if len(stdout.splitlines()) > 10:
            print(f"    {_DIM}... ({len(stdout.splitlines()) - 10} more lines){_RESET}")
    if stderr and not result["success"]:
        for line in stderr.splitlines()[:15]:
            print(f"    {_YELLOW}stderr: {line}{_RESET}")


async def execute_matlab_file(
    ctx: RunContext[ConversionContext],
    matlab_filename: str,
    timeout: int = 60,
) -> dict[str, Any]:
    """Run an original MATLAB .m file using the MATLAB Engine API and capture its output.

    Use this to obtain reference output from the original MATLAB script so you
    can compare it against the converted Python script's output for correctness.
    The captured output is saved to <output_dir>/<stem>_matlab_output.txt.

    Only available when --provider bmw is used (requires MATLAB license).

    Args:
        matlab_filename: Name of the .m file (e.g. 'my_script.m').
        timeout: Maximum seconds to wait for execution (default 60).

    Returns:
        dict with success, stdout, stderr, execution_time, and output_file path.
    """
    matlab_filename = Path(matlab_filename).name
    file_path = ctx.deps.input_dir / matlab_filename

    if not file_path.exists():
        result: dict[str, Any] = {
            "success": False,
            "stdout": "",
            "stderr": f"MATLAB file not found: {file_path}",
            "execution_time": 0.0,
        }
        _log_result(matlab_filename, result)
        return result

    try:
        result = await asyncio.wait_for(
            asyncio.to_thread(
                _run_matlab_script, ctx.deps.input_dir, matlab_filename, timeout
            ),
            timeout=timeout + 5,  # small buffer over MATLAB's own timeout
        )
    except asyncio.TimeoutError:
        result = {
            "success": False,
            "stdout": "",
            "stderr": f"MATLAB execution timed out after {timeout}s",
            "execution_time": float(timeout),
        }
    except ImportError:
        result = {
            "success": False,
            "stdout": "",
            "stderr": (
                "matlab.engine module not available. "
                "Install with: cd <MATLAB_ROOT>/extern/engines/python && pip install ."
            ),
            "execution_time": 0.0,
        }

    # Save output to file
    stem = Path(matlab_filename).stem
    output_file = ctx.deps.output_dir / f"{stem}_matlab_output.txt"
    output_content = ""
    if result.get("stdout"):
        output_content += result["stdout"]
    if result.get("stderr"):
        output_content += f"\n--- STDERR ---\n{result['stderr']}"
    if output_content.strip():
        output_file.write_text(output_content, encoding="utf-8")
        result["output_file"] = str(output_file)

    # Cache in context
    ctx.deps.matlab_outputs[matlab_filename] = result.get("stdout", "")

    # Truncate for agent response
    result["stdout"] = _truncate(result.get("stdout", ""))
    result["stderr"] = _truncate(result.get("stderr", ""))

    _log_result(matlab_filename, result)
    return result
