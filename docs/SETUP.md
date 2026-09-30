# Setup

## Portable environment

Use Python 3.12 on macOS or Linux. Create a virtual environment and install `requirements-dev.txt`. The Streamlit app listens on loopback by default. `make app` uses port 8504. Windows process-group behavior has not been validated; use WSL for portable checks.

## Pkl

Install Pkl from https://pkl-lang.org/main/current/pkl-cli/index.html. Development validation uses Pkl 0.32.1. Set `PKL_BIN` to an absolute executable path if it is not on PATH. `config/default.pkl` is the authoring source. Run `python scripts/export_config.py` after editing; commit the Pkl and generated JSON together. A stale export raises an error. `pkl test config/tests.pkl` checks configuration facts. UI edits additionally pass through Python runtime models; arbitrary user-authored Pkl files are never evaluated.

## Apple Container

Use an Apple silicon Mac with supported macOS 26. Download the official signed installer from https://github.com/apple/container/releases. Development validation targets Container 1.5.0. Start it using `container system start` and install the recommended kernel when prompted. Set `CONTAINER_BIN` if using a nonstandard installation. Verify `container list --format json` succeeds.

Pre-pull the images before timed experiments:

```bash
container image pull ghcr.io/ggml-org/llama.cpp:server
```

The application creates only `lab-...-<random>` containers and removes those exact names. It does not run global prune or delete unrelated containers. Interrupted host processes can leave VMs behind: inspect `container list --all`, then delete only the names from your run. Do not run the live app as a publicly accessible unauthenticated service.

## Model option

The AI reviewer defaults to local TF-IDF retrieval and needs no model. To enable synthesis, supply an HTTP loopback/private-network or HTTPS remote chat-completions endpoint in the UI. Set `LAB_MODEL_API_KEY` in the environment if required; never commit it. The UI sends only after Answer is clicked. A local llama.cpp server is supported. Model licensing and disk/RAM requirements vary.

## Troubleshooting

- Missing runtime: install/start Container; the application will not execute submitted sandbox code on the host.
- First job exceeds deadline: pre-pull the image and retry after verifying runtime health.
- `Pkl snapshot is stale`: regenerate the export using the documented CLI.
- Empty stats: increase probe duration; do not substitute zero usage.
- Public HTTP 403/429: wait for upstream rate limits or use cached/downloaded data. No GitHub token is required for the public catalogue.
- OTLP exporter connection failures: remove the optional OTLP endpoint or start a collector. Local JSONL evidence remains available.
- Model errors: verify `/health`, model identity, available memory, and `/v1/chat/completions` support.

## macOS filesystem access

On macOS, a background virtualization helper may not be able to access files under protected folders such as Documents. Live jobs stage their specific input and workload files into per-run temporary directories before read-only mounting them. The model launcher stages only the selected GGUF file. Install the Container executable in its normal vendor location rather than running the daemon from a protected Documents directory. No broad filesystem-permission change is required by these projects.

## Reproducible small-model download

```bash
python scripts/download_model.py
```

This downloads a commit-pinned public GGUF from Hugging Face and verifies its SHA-256 before renaming the partial file. It is about 101 MiB and is suitable for CPU smoke tests. Open Model server in Streamlit, use the cached GGUF path, and choose Start. The returned endpoint and model name can be used by Benchmark and AI reviewer. Stop returns resources to the runtime. The public GSM8K trial deliberately records this small model's weak answer quality; use a stronger licensed model and a larger sample when evaluating usefulness.
