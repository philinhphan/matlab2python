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
# Convert all .m files in testfiles/ → output/
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
# Default model: openai/gpt-4o
python main.py testfiles/ --provider bmw

# Use a specific model
python main.py testfiles/ --provider bmw --model anthropic/claude-3-7-sonnet
python main.py testfiles/ --provider bmw --model openai/o3-mini
```

All other flags (`-o`, `-f`, `--max-revisions`) work the same regardless of provider.

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
| `openai/gpt-4o` | Default for `--provider bmw` |
| `openai/gpt-4o-mini` | Faster / cheaper |
| `openai/o3-mini` | Reasoning model |
| `anthropic/claude-3-7-sonnet` | Anthropic via BMW gateway |
| `anthropic/claude-haiku-4-5` | Fast Anthropic model |
| `anthropic/claude-sonnet-4` | Latest Anthropic Sonnet |

---

## Environment variables

| Variable | Provider | Description |
|---|---|---|
| `OPENAI_API_KEY` | OpenAI | Standard OpenAI API key |
| `LLM_API_PROD_KEY` | BMW | API product key |
| `CLIENT_ID` | BMW | OAuth client ID |
| `CLIENT_SECRET` | BMW | OAuth client secret |
| `LLM_ACCESS_TOKEN` | BMW | Optional cached access token |
| `LLM_ACCESS_TOKEN_EXP` | BMW | ISO-8601 expiry of cached token |

---

## Project structure

```
matlab2python/
├── main.py                    # CLI entry point
├── requirements.txt
├── .env.example               # Credential template
├── converter/
│   ├── agent.py               # Pydantic AI agent factory
│   ├── bmw_auth.py            # BMW OAuth + CA-cert helper
│   ├── context.py             # ConversionContext dataclass
│   ├── prompts.py             # System prompt + task template
│   ├── stdlib_map.py          # 185-entry MATLAB→Python mapping
│   ├── logging_config.py      # Logfire / Jaeger tracing
│   ├── tools/
│   │   ├── file_tools.py      # read/write .m and .py files
│   │   ├── analysis_tools.py  # pattern analysis, dependency graph
│   │   ├── validation_tools.py# syntax check, pyflakes, import check
│   │   └── knowledge_tools.py # conversion rules, plotting recipes
│   └── utils/
│       └── mat_io.py          # .mat file loader, subtightplot, lighten_color
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
