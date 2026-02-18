"""CLI entry point for the agentic MATLAB-to-Python converter."""

from __future__ import annotations

import argparse
import asyncio
from pathlib import Path

from openai import AsyncOpenAI
from dotenv import load_dotenv
from pydantic_ai.providers.openai import OpenAIProvider

from converter.agent import create_agent
from converter.context import ConversionContext
from converter.prompts import AGENT_TASK_PROMPT_TEMPLATE


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
  python main.py testfiles/ --model gpt-4o-mini

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
        "--model",
        default="gpt-4o-mini",
        help="OpenAI model to use (default: gpt-4o-mini)",
    )
    parser.add_argument(
        "--max-revisions",
        type=int,
        default=5,
        help="Maximum revision attempts per file (default: 5)",
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

    print(f"Input:  {input_dir}")
    print(f"Output: {output_dir}")
    print(f"Model:  {args.model}")
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

    model_name = args.model.removeprefix("openai:")
    client = AsyncOpenAI(max_retries=5)
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

    result = await agent.run(prompt, deps=ctx)

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
