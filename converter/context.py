from __future__ import annotations
from dataclasses import dataclass, field
from pathlib import Path


@dataclass
class ConversionContext:
    input_dir: Path
    output_dir: Path
    target_files: list[str] = field(default_factory=list)          # empty = all .m files
    matlab_sources: dict[str, str] = field(default_factory=dict)   # filename → raw source
    converted_files: dict[str, str] = field(default_factory=dict)  # py_filename → current code
    conversion_errors: dict[str, list[str]] = field(default_factory=dict)
    revision_history: dict[str, list[str]] = field(default_factory=dict)
    known_functions: dict[str, dict] = field(default_factory=dict) # MATLAB fn → {args, returns, file}
    dependency_graph: dict[str, list[str]] = field(default_factory=dict)
    requirements: set[str] = field(default_factory=set)
    conversion_notes: list[str] = field(default_factory=list)       # agent-recorded stubs/warnings
    max_revision_attempts: int = 5
    matlab_encoding: str = "latin-1"                                # German characters in test files
