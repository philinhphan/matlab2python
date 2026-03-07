"""Copy non-code data files from input directory to output directory."""

from __future__ import annotations

import os
import shutil
from pathlib import Path

# Extensions to skip (source code and bytecode)
_SKIP_EXTENSIONS = {".m", ".asv", ".py", ".pyc"}
_SKIP_DIRS = {"__pycache__"}


def setup_output_workspace(input_dir: Path, output_dir: Path) -> dict:
    """Copy non-code files (.mat, .fig, .h5, data dirs) from input to output.

    Walks input_dir recursively and copies everything except MATLAB/Python
    source files, preserving directory structure. This makes the output
    directory self-contained so converted scripts can find their data files.

    Returns summary dict with files_copied, dirs_created, total_size_bytes, items.
    """
    files_copied = 0
    dirs_created = 0
    total_size = 0
    items: list[str] = []

    for root, dirs, files in os.walk(input_dir):
        # Skip __pycache__ directories
        dirs[:] = [d for d in dirs if d not in _SKIP_DIRS]

        rel_root = Path(root).relative_to(input_dir)

        for filename in files:
            ext = Path(filename).suffix.lower()
            if ext in _SKIP_EXTENSIONS:
                continue

            src = Path(root) / filename
            dst = output_dir / rel_root / filename

            dst.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(src, dst)

            size = src.stat().st_size
            total_size += size
            files_copied += 1
            items.append(str(rel_root / filename))

        # Count directories we created (excluding the root)
        for d in dirs:
            dst_dir = output_dir / rel_root / d
            if not dst_dir.exists():
                dst_dir.mkdir(parents=True, exist_ok=True)
                dirs_created += 1

    # Auto-provision utils.py from converter/utils/mat_io.py
    utils_written = _provision_utils(output_dir)

    return {
        "files_copied": files_copied,
        "dirs_created": dirs_created,
        "total_size_mb": round(total_size / (1024 * 1024), 2),
        "items": items,
        "utils_written": utils_written,
    }


def _provision_utils(output_dir: Path) -> bool:
    """Write a robust utils.py into output_dir from converter/utils/mat_io.py."""
    # Locate mat_io.py relative to this file
    mat_io_path = Path(__file__).parent / "utils" / "mat_io.py"
    if not mat_io_path.is_file():
        return False

    source = mat_io_path.read_text(encoding="utf-8")

    # Write to output_dir/utils.py with a module docstring
    utils_path = output_dir / "utils.py"
    header = '"""Pre-provisioned shared utilities for MATLAB-to-Python conversion.\n\nContains mat_to_dict(), lighten_color(), subtightplot().\nDo NOT recreate this file — it is auto-generated.\n"""\n\n'
    utils_path.write_text(header + source, encoding="utf-8")
    return True
