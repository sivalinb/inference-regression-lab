# Architecture

## Data flow

Pkl benchmark matrix → built-in or GSM8K prompts → warmup → bounded concurrent SSE requests → per-request observations → SLO summary → compatible-baseline regression gate. Optional model management runs llama.cpp in Apple Container.

## Implementation decisions

The SSE reader ignores comments and empty records, measures first nonempty content, records content-chunk arrival times, reads usage-only records, and requires an explicit DONE marker. It reports errors instead of substituting synthetic measurements. Aggregate token throughput uses server-reported completion tokens divided by batch wall time; it remains unavailable when usage is missing. It never treats streamed chunks as tokens. Warmups are excluded from timing. A baseline signature includes workload hash, model identifier, request count, concurrency, token limit, and mode. Incompatible reports are rejected rather than compared silently.

## Modules

`app.py` renders Streamlit controls and stores the current report in session state. `engine.py` contains domain logic and typed runtime models. `config/` stores Pkl source and its verified export. `labcore/runtime.py` issues argument-array subprocess calls, captures bounded output, and scopes cleanup to generated job names. `labcore/observability.py` writes event metadata and experiment reports. `labcore/ai.py` retrieves reference evidence and optionally synthesizes a cited answer. `data/sources.json` declares the public inputs and their terms. `workloads/` contains trusted workload entrypoints, where needed. `tests/` covers failure cases and Streamlit workflows.

## Trust boundaries

UI uploads and downloaded source content are data. They do not become system commands or Pkl modules. The sandbox project explicitly permits user Python inside a VM. Other tools execute only checked-in workload entrypoints. Subprocess calls use argument lists without a shell. Source URLs come from a fixed HTTPS catalogue with redirects disabled. Model responses are advisory and cannot trigger container actions.

## Persistence and reproducibility

Run artifacts are local and ignored by Git. Reports retain the mode, input/contract settings, source/config hashes where applicable, raw observations, and calculated decisions. Reproduce a finding by saving the report, pinning runtime/image/model versions, rerunning with the same workload, and comparing independent trials. Generated configuration and dependency versions are committed. For formal benchmarks replace mutable image tags with verified OCI digests.
