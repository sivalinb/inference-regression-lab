# Verified results

Verified on 2026-09-30 UTC (2026-09-29 Mountain Time). This page reports observed development checks, not production reliability guarantees. The committed JSON evidence contains synthetic workloads, public-source metadata, and measured results. Secrets, local usernames, and source-cache contents are excluded.

## Portable checks

- `pytest -q`: **24 passed**, including the Streamlit primary workflow.
- `python scripts/evaluate.py`: all domain checks passed; retrieval hit@3 was 1.0 on five authored questions, and the unrelated-question abstention check passed.
- Pkl 0.32.1: valid configuration tests passed; invalid CPU allocation is rejected by the Python test suite.
- `ruff check .`: passed.

[portable-checks.json](evidence/portable-checks.json) preserves command results. The five retrieval questions are a small diagnostic suite, not a broad RAG quality benchmark. The default reviewer performs deterministic retrieval; no LLM is required for portable checks.

[Environment and OCI digests](evidence/environment.json) identify the tested dependencies and live image revisions. [GitHub Actions](https://github.com/sivalinb/inference-regression-lab/actions) independently reports the current portable CI status. Ordinary Linux CI does not run Apple Container workloads.

## Real model and public dataset

A CPU-only llama.cpp server ran inside Apple Container with the public SmolLM2-135M-Instruct Q4_K_M model. The pinned model download is about 101 MiB; its SHA-256 and source commit are in [model.json](evidence/model.json). The cached image was llama.cpp b11243. No GPU acceleration was used.

| Workload | Successful requests | Errors | Observed p95 TTFT | Numeric exact match |
|---|---:|---:|---:|---:|
| Four tiny built-in prompts, repeated | 12/12 | 0 | 109.96 ms | 6/6 numeric cases |
| First four public GSM8K test questions | 4/4 | 0 | 214.29 ms | 0/4 |

The first workload had concurrency 2 and 48 maximum generated tokens; GSM8K used concurrency 2 and 64 maximum generated tokens. The two explanation prompts are excluded from numeric scoring. The poor GSM8K result is retained: this small model and short generation budget are useful for testing the benchmark, not evidence of strong mathematical reasoning. Passing latency/error SLOs does not imply passing quality.

See [live-inference.json](evidence/live-inference.json) and [gsm8k.json](evidence/gsm8k.json) for per-request observations, usage counts, workload hashes, and settings. Throughput uses reported completion tokens, not SSE chunk counts. Twelve and four requests are smoke samples; their descriptive percentiles are not stable tail-latency estimates or hardware comparisons. Prompt caching and warmup can affect these numbers.

## Cancellation and AI reviewer

The client cancellation probe closed a real stream after two content chunks and returned `cancelled`; see [cancellation.json](evidence/cancellation.json). It does not measure server-side resource reclamation. The optional AI reviewer was also called against this model. Its answer failed the citation-ID gate, so the UI correctly abstained and exposed the retrieved evidence. See [ai-reviewer.json](evidence/ai-reviewer.json). The gate checks citation structure/membership, not factual entailment.

## Reproduce

Run `python scripts/download_model.py`, start the server from the Model server tab, and run a Live endpoint benchmark. The managed launcher reports the usable address and model identifier. It tries loopback forwarding first, then the VM's private address when forwarding is unavailable. Use Public sources to fetch GSM8K, select it as the workload, and keep raw responses. Stop the managed model using the same tab when finished.

## Public source verification

All ten catalogue entries downloaded successfully during verification, including USGS, NAB CPU/taxi, GSM8K, OpenMetrics, OTel semantic conventions, Pkl/Container releases, Apple runtime resource documentation, and node_exporter documentation. [public-sources.json](evidence/public-sources.json) records retrieval times, byte counts, hashes, URLs, and upstream terms. Documentation and release metadata are reference material, not empirical workload measurements. Downloaded source contents remain untracked and are not relicensed by this repository.
