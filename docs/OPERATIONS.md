# Observability, AI, and operation

## Local artifacts

Every instrumented operation creates an event in `artifacts/events.jsonl` with a run ID, trace ID, operation, mode, status, and duration. Reports are saved as JSON with random filenames and a SHA-256 checksum returned by the recorder. `artifacts/metrics.prom` contains Prometheus counters/histograms for the current process lifetime. Streamlit reruns share a cached recorder. Restarting the process resets in-memory counters; audit files persist.

Audit events intentionally exclude API keys, prompts, uploaded bytes, and arbitrary exception text. Experiment reports can contain requested workload output and model responses, so review them before sharing. Artifacts are not committed by default. The optional OTLP/HTTP trace exporter is enabled with `OTEL_EXPORTER_OTLP_ENDPOINT`; leave it unset for local-only use. A collector can scrape or receive the generated signals through your preferred stack.

## AI reviewer

The default path is deterministic TF-IDF retrieval over a small cited knowledge base. It is useful for finding relevant engineering guidance and is labeled as retrieval, not LLM inference. The Answer action can optionally call a local or remote chat-completions endpoint. The model receives the question, retrieved evidence, and current experiment report. No model request runs automatically. Public remote endpoints require HTTPS; explicitly configured private VM addresses also support HTTP; keys are read from the environment and excluded from logs.

Generated answers must contain allowed citation IDs. Missing or unknown IDs cause rejection. This is a structural check, not a truth verifier: a valid citation can still be misused. The AI reviewer cannot launch jobs, change policies, or override release decisions. Retrieval evals run without credentials. Use a separate labeled dataset and human review to assess synthesis quality.

## Operating model

This is a single-user local lab. Bind to loopback. Use a dedicated model directory and disposable data. Preserve report modes. Start/stop only lab-owned runtime resources. Pin dependencies and images before reproducing benchmarks. Keep secrets in environment variables or untracked Streamlit secrets, never in Git. CI runs portable tests, lint checks, Pkl validation, and evals; live execution is opt-in.
