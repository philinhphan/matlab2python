# matlab2python

Agentic MATLAB-to-Python converter powered by [Pydantic AI](https://ai.pydantic.dev/).

The agent reads `.m` source files, converts them to idiomatic Python (NumPy/SciPy/Matplotlib), validates syntax and imports, and iterates until the output is clean. It supports two LLM back-ends: the standard OpenAI API and the BMW internal LLM API.

---

## Requirements

- Python 3.11+
- An OpenAI API key **or** BMW LLM API credentials

---

## Setup

```bash
# 1. Clone
git clone <repo-url>
cd matlab2python

# 2. Create and activate a virtual environment
python -m venv venv
source venv/bin/activate   # Windows: venv\Scripts\activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Configure credentials
cp .env.example .env
# Edit .env and fill in your API key(s)
```

---

## Usage

### OpenAI (default)

```bash
# Convert all .m files in testfiles/ -> output/
python main.py testfiles/

# Choose a different output directory
python main.py testfiles/ -o converted/

# Convert specific files only
python main.py testfiles/ -f script1.m script2.m

# Use a different model
python main.py testfiles/ --model gpt-4o

# Allow more self-correction passes per file
python main.py testfiles/ --max-revisions 8
```

### BMW LLM API

Add the BMW credentials to your `.env` (see [BMW Setup](#bmw-setup) below), then:

```bash
# Default model: openai/gpt-5-mini
python main.py testfiles/ --provider bmw

# Use a specific model
python main.py testfiles/ --provider bmw --model anthropic/claude-3-7-sonnet
python main.py testfiles/ --provider bmw --model openai/o3-mini
```

All other flags (`-o`, `-f`, `--max-revisions`) work the same regardless of provider.

---

## How It Works

The converter is built as an autonomous **Pydantic AI agent** that drives the entire conversion process end-to-end. Rather than a simple template-based transpiler, it uses an LLM as its reasoning engine and equips it with a suite of specialized tools to read, write, analyze, and validate code.

### Architecture Overview

```
main.py (CLI)
  |
  v
create_agent()          <-- agent.py: builds Pydantic AI Agent with all tools
  |
  +-- SYSTEM_PROMPT     <-- prompts.py: 14k-char instruction set with 14 conversion rules
  +-- ConversionContext  <-- context.py: shared state (sources, outputs, errors, revision history)
  +-- 16 registered tools across 4 modules:
  |     file_tools.py       (6 tools: read/write/list files, record notes)
  |     analysis_tools.py   (3 tools: pattern detection, function signatures, dependency graph)
  |     validation_tools.py (5 tools: syntax check, pyflakes, indexing audit, import check, error annotator)
  |     knowledge_tools.py  (3 tools: stdlib map lookup, conversion rules, plotting recipes)
  |
  v
agent.run(prompt, deps=ctx)   <-- LLM drives the conversion autonomously
```

### Conversion Pipeline

The agent operates in **four phases**, calling its tools autonomously:

#### Phase 1: Analysis

The agent scans the input directory and builds a picture of the codebase:

1. **`list_matlab_files`** discovers all `.m` files (excluding `.asv` backups).
2. **`read_matlab_file`** loads each file using latin-1 encoding (for German characters) and caches the source.
3. **`analyze_matlab_patterns`** runs 12 regex-based detectors on each file, flagging patterns like dynamic struct access, arithmetic column indexing, polar plots, `waitbar`, `uigetfile`, etc.
4. **`extract_function_signatures`** parses MATLAB function headers to build a cross-file function registry.
5. **`build_dependency_graph`** cross-references function calls across files and produces a topological sort for conversion order.
6. **`get_conversion_rule`** is consulted for each flagged pattern (18 rules covering indexing, structs, .mat I/O, GUI stubs, plotting, etc.).

#### Phase 2: Per-File Conversion (with self-correction loop)

For each file, in dependency order:

1. The agent translates the MATLAB source to Python and writes it via **`write_python_file`**.
2. **`validate_python_syntax`** compiles the output with `compile()`. On failure, **`annotate_error_in_source`** highlights the error location with context lines.
3. **`run_pyflakes`** detects undefined names and unused imports via the Pyflakes checker API.
4. **`check_numpy_indexing`** applies heuristic checks for common 1-based indexing mistakes: `range(1,N)` loop vars used as direct indices, `[:, 1]` patterns, `np.where()` without `[0]`, and arithmetic index expressions missing a `-1` offset.
5. **`validate_imports`** AST-parses the file to verify all referenced names have matching imports or definitions.
6. The agent rewrites and re-validates up to `--max-revisions` times (default 5). If it cannot produce clean output, it writes the best version with a `# VALIDATION FAILED:` comment.
7. **`record_conversion_note`** logs any stubs, warnings, or manual-review items to `CONVERSION_NOTES.md`.

#### Phase 3: Cross-File Integration

The agent checks that:
- Function calls across files use consistent Python names.
- Shared helpers (`mat_to_dict`, `subtightplot`, `lighten_color`) are properly imported from `converter/utils/mat_io.py` or inlined.
- All import statements are complete.

#### Phase 4: Finalize

1. **`write_requirements_txt`** generates a `requirements.txt` with the libraries used (numpy, scipy, matplotlib, tqdm, plus any extras).
2. The agent writes a summary of all files converted, stubs created, and patterns encountered.

### Knowledge Base

The agent draws on three embedded knowledge sources:

- **`stdlib_map.py`** (185 entries): A lookup table mapping MATLAB built-in functions to their Python equivalents with import requirements and usage notes (e.g., `interp1` -> `scipy.interpolate.interp1d`).
- **Conversion rules** (18 patterns): Detailed, example-rich recipes for tricky patterns like arithmetic column indexing, `waitbar` -> `tqdm`, `uigetfile` -> `input()` stubs, polar plots, etc.
- **Plotting recipes** (20 commands): Matplotlib equivalents for MATLAB plot types including polar, semilog, grouped bar, contourf, imagesc, quiver, and more.

### Key Conversion Rules

The system prompt encodes 14 conversion rules. The most critical:

| Rule | What it handles |
|---|---|
| **Indexing** | 1-based -> 0-based for all index operations, slices, and loop variables |
| **Arithmetic column index** | `ZArrayV(:, 2*kk-1)` -> `ZArrayV[:, 2*kk-2]` (subtract 1 from the final computed start index) |
| **Dynamic struct access** | `s.(varname)` -> `s[varname]`, `s.(['Z' num2str(kk)])` -> `s[f'Z{kk}']` |
| **.mat file I/O** | `load()`/`save()` -> `scipy.io.loadmat()`/`savemat()` with `mat_to_dict()` cleanup |
| **GUI stubs** | `uigetfile` -> `input()`, `waitbar` -> `tqdm`, `assignin` -> removed with note |
| **Plotting** | Always object-oriented matplotlib (`ax.plot()`, not `plt.plot()`) |
| **Polar plots** | Require `subplot_kw={'projection': 'polar'}` |
| **String operations** | MATLAB concatenation `[a b]` -> f-strings, `sprintf` -> f-strings |
| **Multiple returns** | `[out1, out2] = fn(x)` -> `out1, out2 = fn(x)` |

### Shared Utilities

`converter/utils/mat_io.py` provides three helpers that are either inlined into converted files or imported:

- **`mat_to_dict(mat)`**: Cleans `scipy.io.loadmat` output by removing metadata keys (`__header__`, etc.) and squeezing single-element arrays to scalars.
- **`subtightplot(n_rows, n_cols, idx, ...)`**: MATLAB-compatible subplot function using `matplotlib.gridspec.GridSpec` with fine-grained margin control.
- **`lighten_color(color, amount)`**: Lightens a matplotlib color by mixing with white (equivalent to MATLAB custom `Light()` function).

### Observability

The converter emits **OpenTelemetry traces** via [Logfire](https://logfire.pydantic.dev/) to a local Jaeger instance. This provides:

- A span tree for each `agent.run()` call (model calls, tool invocations, retries)
- Individual HTTP request traces for the OpenAI client (token counts, latencies)
- Full visibility into the agent's decision-making process

---

## BMW Setup

BMW's LLM API uses an OpenAI-compatible interface with OAuth authentication and a corporate CA certificate.

### 1. Credentials

Obtain the following from your BMW WebEAM registration and add them to `.env`:

| Variable | Description |
|---|---|
| `LLM_API_PROD_KEY` | API product key (`x-apikey` header) |
| `CLIENT_ID` | OAuth client ID |
| `CLIENT_SECRET` | OAuth client secret |

### 2. Optional: cache a pre-fetched token

To skip the OAuth round-trip on startup, you can supply a pre-fetched token:

```bash
# Fetch a token once and print it
python - <<'EOF'
from converter.bmw_auth import get_access_token
import os; from dotenv import load_dotenv; load_dotenv()
token, expires_in = get_access_token(os.environ["CLIENT_ID"], os.environ["CLIENT_SECRET"])
from datetime import datetime, timezone, timedelta
exp = datetime.now(timezone.utc) + timedelta(seconds=expires_in)
print(f"LLM_ACCESS_TOKEN={token}")
print(f"LLM_ACCESS_TOKEN_EXP={exp.isoformat()}")
EOF
```

Paste the output into your `.env`. The converter will reuse the cached token automatically and refresh it when expired.

### 3. CA certificate

The BMW CA certificate (`BMW_Trusted_Certificates_Latest.pem`) is downloaded automatically on first run and cached locally. No manual action needed.

### Available BMW models

| Model ID | Notes |
|---|---|
| `openai/gpt-5-mini` | Default for `--provider bmw` |
| `openai/gpt-4o` | High capability model |
| `openai/gpt-4o-mini` | Faster / cheaper |
| `openai/o3-mini` | Reasoning model |
| `anthropic/claude-3-7-sonnet` | Anthropic via BMW gateway |
| `anthropic/claude-haiku-4-5` | Fast Anthropic model |
| `anthropic/claude-sonnet-4` | Latest Anthropic Sonnet |

---

## Environment Variables

| Variable | Provider | Description |
|---|---|---|
| `OPENAI_API_KEY` | OpenAI | Standard OpenAI API key |
| `LLM_API_PROD_KEY` | BMW | API product key |
| `CLIENT_ID` | BMW | OAuth client ID |
| `CLIENT_SECRET` | BMW | OAuth client secret |
| `LLM_ACCESS_TOKEN` | BMW | Optional cached access token |
| `LLM_ACCESS_TOKEN_EXP` | BMW | ISO-8601 expiry of cached token |

---

## Project Structure

```
matlab2python/
├── main.py                    # CLI entry point
├── requirements.txt
├── .env.example               # Credential template
├── converter/
│   ├── agent.py               # Pydantic AI agent factory (16 tools registered)
│   ├── bmw_auth.py            # BMW OAuth + CA-cert helper
│   ├── context.py             # ConversionContext dataclass (shared agent state)
│   ├── prompts.py             # System prompt (14 rules) + task template
│   ├── stdlib_map.py          # 185-entry MATLAB -> Python mapping
│   ├── logging_config.py      # Logfire / Jaeger tracing
│   ├── tools/
│   │   ├── file_tools.py      # read/write .m and .py files, record notes
│   │   ├── analysis_tools.py  # pattern analysis, function signatures, dependency graph
│   │   ├── validation_tools.py# syntax check, pyflakes, indexing audit, import check
│   │   └── knowledge_tools.py # conversion rules, stdlib map, plotting recipes
│   └── utils/
│       └── mat_io.py          # mat_to_dict, subtightplot, lighten_color helpers
├── testfiles/                 # Example MATLAB scripts (input)
└── output/                    # Converted Python files (generated)
```

---

## Tracing (optional)

The converter emits OpenTelemetry traces via [Logfire](https://logfire.pydantic.dev/) to a local Jaeger instance. A pre-built Jaeger binary for macOS (arm64) is included.

```bash
# Start Jaeger
./jaeger-2.15.1-darwin-arm64/jaeger &

# Open the Jaeger UI
open http://localhost:16686
```

Traces appear under the `matlab2python` service after each conversion run.

---

## Notes

- MATLAB source files are expected to be **latin-1** encoded (common in legacy German engineering code).
- Column indexing is translated from 1-based MATLAB (`x(:, 2*k-1)`) to 0-based NumPy (`x[:, 2*k-2]`).
- `subtightplot` and `.mat` file loading utilities are provided in `converter/utils/mat_io.py`.
- German comments in source files are automatically translated to English during conversion.
- GUI functions (`uigetfile`, `waitbar`, `assignin`) are replaced with CLI-friendly stubs.
- Dangerous MATLAB patterns like `eval(sprintf(...))` are converted to safe dict dispatch -- never to Python `eval()`.
