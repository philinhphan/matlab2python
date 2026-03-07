"""CLI entry point for the agentic MATLAB-to-Python converter."""

from __future__ import annotations

import argparse
import asyncio
from pathlib import Path

from openai import AsyncOpenAI
from dotenv import load_dotenv
from pydantic_ai.providers.openai import OpenAIProvider
from pydantic_ai.usage import UsageLimits

from converter.agent import create_agent
from converter.context import ConversionContext
from converter.logging_config import configure_logfire
from converter.prompts import AGENT_TASK_PROMPT_TEMPLATE
from converter.workspace import setup_output_workspace

_OPENAI_DEFAULT_MODEL = "gpt-5-mini"
_BMW_DEFAULT_MODEL = "openai/gpt-4o"


async def main() -> None:
    load_dotenv()

    parser = argparse.ArgumentParser(
        description="Agentic MATLAB→Python converter",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Convert all .m files in testfiles/ to output/
  python main.py testfiles/

  # Convert to specific output directory
  python main.py testfiles/ -o converted/

  # Convert only specific files
  python main.py testfiles/ -f G_MHS_Berechnung_v03.m G_Emergenz_Auswertung_ANTRIEB_BEV_v07.m

  # Use a different model
  python main.py testfiles/ --model gpt-5-mini

  # Use BMW LLM API (reads credentials from .env)
  python main.py testfiles/ --provider bmw

  # Use BMW API with a specific model
  python main.py testfiles/ --provider bmw --model anthropic/claude-3-7-sonnet

  # Allow more revision attempts
  python main.py testfiles/ --max-revisions 8
""",
    )
    parser.add_argument(
        "input_dir",
        type=Path,
        help="Directory containing MATLAB .m files",
    )
    parser.add_argument(
        "--output-dir",
        "-o",
        type=Path,
        default=None,
        help="Output directory for converted Python files (default: <input_dir>/../output)",
    )
    parser.add_argument(
        "--files",
        "-f",
        nargs="*",
        default=[],
        metavar="FILE",
        help="Specific .m files to convert (default: all .m files in input_dir)",
    )
    parser.add_argument(
        "--provider",
        choices=["openai", "bmw"],
        default="openai",
        help="LLM provider to use: 'openai' (default) or 'bmw'",
    )
    parser.add_argument(
        "--model",
        default=None,
        help=(
            f"Model to use. OpenAI default: {_OPENAI_DEFAULT_MODEL!r}. "
            f"BMW default: {_BMW_DEFAULT_MODEL!r}."
        ),
    )
    parser.add_argument(
        "--max-revisions",
        type=int,
        default=5,
        help="Maximum revision attempts per file (default: 5)",
    )
    parser.add_argument(
        "--trace",
        action="store_true",
        help="Enable OpenTelemetry tracing (requires Jaeger on localhost:4318)",
    )
    args = parser.parse_args()

    input_dir = args.input_dir.resolve()
    if not input_dir.exists():
        parser.error(f"Input directory does not exist: {input_dir}")
    if not input_dir.is_dir():
        parser.error(f"Input path is not a directory: {input_dir}")

    output_dir = args.output_dir or input_dir.parent / "output"
    output_dir = output_dir.resolve()
    output_dir.mkdir(parents=True, exist_ok=True)

    # Resolve model default per provider
    if args.model is not None:
        model_arg = args.model
    elif args.provider == "bmw":
        model_arg = _BMW_DEFAULT_MODEL
    else:
        model_arg = _OPENAI_DEFAULT_MODEL

    print(f"Input:    {input_dir}")
    print(f"Output:   {output_dir}")
    print(f"Provider: {args.provider}")
    print(f"Model:    {model_arg}")
    print(f"Max revisions: {args.max_revisions}")
    if args.files:
        print(f"Files:  {', '.join(args.files)}")
    else:
        print("Files:  all .m files")
    print()

    ctx = ConversionContext(
        input_dir=input_dir,
        output_dir=output_dir,
        target_files=args.files or [],
        max_revision_attempts=args.max_revisions,
    )

    # Copy data files to output so converted scripts can find them
    ws = setup_output_workspace(input_dir, output_dir)
    ctx.workspace_ready = True
    print(f"Workspace: copied {ws['files_copied']} data files ({ws['total_size_mb']} MB) to {output_dir}")
    print()

    if args.provider == "bmw":
        import os
        from converter.bmw_auth import create_bmw_openai_client
        client = create_bmw_openai_client(
            api_key=os.environ["LLM_API_PROD_KEY"],
            client_id=os.environ["CLIENT_ID"],
            client_secret=os.environ["CLIENT_SECRET"],
            cached_token=os.environ.get("LLM_ACCESS_TOKEN"),
            cached_token_exp=os.environ.get("LLM_ACCESS_TOKEN_EXP"),
        )
        model_name = model_arg  # e.g. "openai/gpt-4o" — no prefix stripping needed
    else:
        client = AsyncOpenAI(max_retries=5)
        model_name = model_arg.removeprefix("openai:")

    if args.trace:
        configure_logfire(service_name="matlab2python", openai_client=client)
    provider = OpenAIProvider(openai_client=client)
    agent = create_agent(model=model_name, provider=provider)

    prompt = AGENT_TASK_PROMPT_TEMPLATE.format(
        input_dir=ctx.input_dir,
        output_dir=ctx.output_dir,
        file_list=", ".join(ctx.target_files) if ctx.target_files else "all .m files",
        max_attempts=ctx.max_revision_attempts,
    )

    print("Starting conversion agent...\n")
    print("=" * 60)

    actual_m_count = sum(1 for _ in input_dir.rglob("*.m"))
    file_count = max(len(ctx.target_files), actual_m_count, 5)
    result = await agent.run(
        prompt,
        deps=ctx,
        usage_limits=UsageLimits(request_limit=25 * file_count),
    )

    print("=" * 60)
    print("\nAgent output:")
    print(result.output)

    print(f"\n\nConversion complete!")
    print(f"Output files: {output_dir}")
    if ctx.conversion_notes:
        print(f"\nConversion notes ({len(ctx.conversion_notes)}):")
        for note in ctx.conversion_notes:
            print(f"  - {note}")


if __name__ == "__main__":
    asyncio.run(main())
