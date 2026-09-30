# Inference Regression Lab

[![Verify](https://github.com/sivalinb/inference-regression-lab/actions/workflows/ci.yml/badge.svg)](https://github.com/sivalinb/inference-regression-lab/actions/workflows/ci.yml)

Inference changes need reproducible client measurements, a compatible baseline, and explicit quality checks. This application ties a Pkl benchmark contract to raw streaming observations.

Python · Streamlit · Pkl · Apple Container · evaluation evidence · OpenTelemetry

## Start here

```bash
python3.12 -m venv .venv
source .venv/bin/activate
pip install -r requirements-dev.txt
streamlit run app.py --server.port 8504
```

The interface opens at http://127.0.0.1:8504. Portable demos work without a model, API key, Pkl executable, or container runtime. The configuration fallback is a checked export whose source hash must match the committed Pkl source. Every report identifies its mode.

## Walkthrough

1. Run Protocol replay to inspect the UI and report schema without a model. Those numbers are synthetic.
2. Run `python scripts/download_model.py` to fetch a pinned GGUF with SHA-256 verification, or obtain another GGUF from a trusted model registry. A small SmolLM2-135M quantization is sufficient for infrastructure testing; it is not expected to solve GSM8K well.
3. Open Model server, select the absolute GGUF path, and Start isolated model server.
4. Switch to Live model endpoint and run a benchmark against the displayed endpoint.
5. Save a session baseline, rerun identical settings, and compare. Upload saved evidence JSON to compare across sessions.
6. Fetch GSM8K and select its questions for a numeric exact-match evaluation.
7. Test client cancellation. Stop the managed model server when finished.

## Architecture

Pkl benchmark matrix → built-in or GSM8K prompts → warmup → bounded concurrent SSE requests → per-request observations → SLO summary → compatible-baseline regression gate. Optional model management runs llama.cpp in Apple Container.

The Streamlit UI calls pure Python engines; each repository vendors a small `labcore` package so cloning this repository is sufficient. No sibling repository is required.

## CLI and checks

```bash
python scripts/run.py
python scripts/run.py --endpoint http://127.0.0.1:8080/v1 --model local
pytest -q
python scripts/evaluate.py
python scripts/export_config.py   # requires pkl on PATH or PKL_BIN
```

## Observed verification

24 automated tests passed locally. A real CPU model served 12/12 smoke requests. Four public GSM8K requests completed but scored 0/4; the quality failure is documented. See [verified results and evidence](docs/VALIDATION.md) for settings, provenance, and limitations.

## Documentation

- [Setup and live runtime](docs/SETUP.md)
- [Architecture and decisions](docs/ARCHITECTURE.md)
- [Learning walkthrough](docs/WALKTHROUGH.md)
- [Evaluation methodology](docs/EVALUATION.md)
- [Public sources and licenses](docs/DATA_SOURCES.md)
- [Observability and AI](docs/OPERATIONS.md)
- [Security and limitations](docs/SECURITY.md)
- [Verified results](docs/VALIDATION.md)

MIT-licensed project code. External datasets and references retain their own terms. Public inputs are fetched explicitly and kept under ignored `artifacts/`; no private production telemetry is included.
