# Evaluation methodology

Portable tests use an independent local SSE fixture to exercise first-token handling, usage records, malformed payloads, error handling, and cancellation. That fixture is not a model. Public GSM8K questions supply numeric reference answers; exact-match extracts the final numeric answer and is a narrow metric that can over/under-credit free-form reasoning. Keep raw responses for audit. Citation validation on the separate AI reviewer only checks referenced IDs, not the truth of generated text.

## Portable automated checks

Run `pytest -q` and `python scripts/evaluate.py`. Pytest covers independent expected outcomes and boundary conditions, while Streamlit AppTest drives a visible workflow and checks for uncaught exceptions. Pkl tests exercise valid configuration and the Python suite rejects invalid configuration/inputs. The retrieval evaluation uses hand-authored held-out questions, expected evidence IDs, top-three hit rate, and an unrelated question requiring abstention.

## Live verification

Run `python scripts/run.py --live` where supported on an Apple silicon Mac. Live work is intentionally excluded from ordinary Linux CI. A manual macOS workflow is supplied for an explicitly provisioned self-hosted runner. Review the checkout before running it; no pull-request trigger dispatches arbitrary code onto a personal Mac.

## Reporting

Keep the actual pass/fail result, sample count, environment, and raw evidence. A failed negative-control workload may be the expected test outcome; a failed runtime setup is not. Synthetic fixtures test logic, not real-world performance. Simulation invariants do not establish production guarantees. Local model quality scores are bounded by the prompt sample and scoring rule. Retrieval hit rate does not measure generated-answer factuality.
