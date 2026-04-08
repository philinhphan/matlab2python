"""Pydantic AI agent for MATLAB-to-Python conversion."""

from __future__ import annotations

from pydantic_ai import Agent
from pydantic_ai.models.openai import OpenAIChatModel
from pydantic_ai.providers.openai import OpenAIProvider

from converter.context import ConversionContext
from converter.prompts import SYSTEM_PROMPT
from converter.tools.analysis_tools import (
    analyze_matlab_patterns,
    build_dependency_graph,
    extract_function_signatures,
    inspect_mat_file,
    list_mat_files,
)
from converter.tools.file_tools import (
    get_error_lessons,
    list_matlab_files,
    read_converted_file,
    read_matlab_file,
    record_conversion_note,
    write_python_file,
    write_requirements_txt,
)
from converter.tools.knowledge_tools import (
    get_conversion_rule,
    get_matlab_stdlib_mapping,
    get_plotting_recipe,
)
from converter.tools.validation_tools import (
    annotate_error_in_source,
    check_numpy_indexing,
    run_pyflakes,
    validate_imports,
    validate_python_syntax,
)
from converter.tools.execution_tools import execute_python_file
from converter.tools.matlab_engine_tools import execute_matlab_file

_CONTEXT_TOOLS = [
    list_matlab_files,
    read_matlab_file,
    write_python_file,
    read_converted_file,
    write_requirements_txt,
    record_conversion_note,
    get_error_lessons,
    analyze_matlab_patterns,
    extract_function_signatures,
    build_dependency_graph,
    inspect_mat_file,
    list_mat_files,
    validate_python_syntax,
    run_pyflakes,
    check_numpy_indexing,
    validate_imports,
    annotate_error_in_source,
    execute_python_file,
]

_PLAIN_TOOLS = [
    get_matlab_stdlib_mapping,
    get_conversion_rule,
    get_plotting_recipe,
]


def create_agent(
    model: str = "gpt-5-mini",
    provider: OpenAIProvider | None = None,
    provider_name: str = "openai",
) -> Agent[ConversionContext, str]:
    """Create and return the conversion agent with all tools registered.

    Call this after load_dotenv() so the OpenAI API key is available.
    Pass a pre-built provider (e.g. with max_retries) to control the HTTP client.
    """
    if provider is not None:
        model_name = model.removeprefix("openai:")
        model_obj = OpenAIChatModel(model_name=model_name, provider=provider)
        a: Agent[ConversionContext, str] = Agent(
            model_obj,
            deps_type=ConversionContext,
            instructions=SYSTEM_PROMPT,
        )
    else:
        model_id = model if ":" in model else f"openai:{model}"
        a = Agent(
            model_id,
            deps_type=ConversionContext,
            instructions=SYSTEM_PROMPT,
        )
    for _tool in _CONTEXT_TOOLS:
        a.tool(_tool)
    for _plain_tool in _PLAIN_TOOLS:
        a.tool_plain(_plain_tool)

    # MATLAB Engine tool — only available with BMW provider (requires MATLAB license)
    if provider_name == "bmw":
        a.tool(execute_matlab_file)

    return a
