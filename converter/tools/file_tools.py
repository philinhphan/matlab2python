"""File I/O tools for reading MATLAB sources and writing Python outputs."""

from __future__ import annotations

from pathlib import Path

from pydantic_ai import RunContext

from converter.context import ConversionContext


async def list_matlab_files(ctx: RunContext[ConversionContext]) -> list[str]:
    """List all .m files in the input directory (excluding .asv backup files).

    If target_files is set on the context, returns only those files.
    """
    input_dir = ctx.deps.input_dir
    if ctx.deps.target_files:
        return ctx.deps.target_files

    files = sorted(
        p.name
        for p in input_dir.iterdir()
        if p.suffix == ".m" and not p.name.endswith(".asv")
    )
    return files


async def read_matlab_file(ctx: RunContext[ConversionContext], filename: str) -> str:
    """Read a MATLAB source file from the input directory.

    Uses latin-1 encoding to handle German characters. Caches in ctx.deps.matlab_sources.
    Returns the raw MATLAB source code.
    """
    if filename in ctx.deps.matlab_sources:
        return ctx.deps.matlab_sources[filename]

    path = ctx.deps.input_dir / filename
    if not path.exists():
        # Try without extension
        alt = ctx.deps.input_dir / (filename + ".m")
        if alt.exists():
            path = alt
        else:
            return f"ERROR: File not found: {path}"

    content = path.read_text(encoding=ctx.deps.matlab_encoding)
    ctx.deps.matlab_sources[filename] = content
    return content


async def write_python_file(
    ctx: RunContext[ConversionContext],
    python_filename: str,
    content: str,
) -> str:
    """Write Python code to the output directory.

    Appends to revision_history and updates converted_files cache.
    Returns confirmation message with output path.
    """
    # Strip directory components — the LLM sometimes includes the output dir in the filename
    python_filename = Path(python_filename).name
    output_path = ctx.deps.output_dir / python_filename
    output_path.write_text(content, encoding="utf-8")

    ctx.deps.converted_files[python_filename] = content

    if python_filename not in ctx.deps.revision_history:
        ctx.deps.revision_history[python_filename] = []
    ctx.deps.revision_history[python_filename].append(content)

    revision_num = len(ctx.deps.revision_history[python_filename])
    return f"Written: {output_path} (revision {revision_num})"


async def read_converted_file(
    ctx: RunContext[ConversionContext],
    python_filename: str,
) -> str:
    """Read a previously converted Python file from the output directory.

    Used during revision cycles to inspect the current state.
    """
    # Strip directory components — the LLM sometimes includes the output dir in the filename
    python_filename = Path(python_filename).name

    # Check in-memory cache first
    if python_filename in ctx.deps.converted_files:
        return ctx.deps.converted_files[python_filename]

    output_path = ctx.deps.output_dir / python_filename
    if not output_path.exists():
        return f"ERROR: Converted file not found: {output_path}"

    content = output_path.read_text(encoding="utf-8")
    ctx.deps.converted_files[python_filename] = content
    return content


async def write_requirements_txt(ctx: RunContext[ConversionContext]) -> str:
    """Write a requirements.txt based on the libraries used in the conversion.

    Merges base requirements with any added during conversion.
    """
    base_requirements = {
        "numpy>=1.26.0",
        "scipy>=1.13.0",
        "matplotlib>=3.9.0",
        "tqdm>=4.66.0",
    }
    all_requirements = base_requirements | ctx.deps.requirements

    # Sort and write
    lines = sorted(all_requirements)
    content = "\n".join(lines) + "\n"

    output_path = ctx.deps.output_dir / "requirements.txt"
    output_path.write_text(content, encoding="utf-8")
    return f"Written: {output_path} ({len(lines)} packages)"


async def record_conversion_note(
    ctx: RunContext[ConversionContext],
    note: str,
) -> str:
    """Record a conversion note (stub warning, manual review needed, etc.).

    These notes are written to CONVERSION_NOTES.md at the end of conversion.
    """
    ctx.deps.conversion_notes.append(note)
    # Also write/update the notes file immediately
    notes_path = ctx.deps.output_dir / "CONVERSION_NOTES.md"
    all_notes = ["# Conversion Notes\n"]
    all_notes.extend(f"- {n}\n" for n in ctx.deps.conversion_notes)
    notes_path.write_text("".join(all_notes), encoding="utf-8")
    return f"Note recorded: {note}"
