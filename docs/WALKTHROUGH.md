# Learning walkthrough

## Guided experiment

1. Run Protocol replay to inspect the UI and report schema without a model. Those numbers are synthetic.
2. Run `python scripts/download_model.py` to fetch a pinned GGUF with SHA-256 verification, or obtain another GGUF from a trusted model registry. A small SmolLM2-135M quantization is sufficient for infrastructure testing; it is not expected to solve GSM8K well.
3. Open Model server, select the absolute GGUF path, and Start isolated model server.
4. Switch to Live model endpoint and run a benchmark against the displayed endpoint.
5. Save a session baseline, rerun identical settings, and compare. Upload saved evidence JSON to compare across sessions.
6. Fetch GSM8K and select its questions for a numeric exact-match evaluation.
7. Test client cancellation. Stop the managed model server when finished.

## Questions to answer in your portfolio write-up

1. What concrete failure does this experiment expose?
2. Which checks happen before execution, and which need runtime observations?
3. Which input, configuration, image, and model versions were used?
4. What did the positive and negative controls demonstrate?
5. Where could the measurements be misleading?
6. Which follow-up experiment would challenge your conclusion?

## Suggested demonstration

Record a three-minute walkthrough: explain the failure in one sentence, run a baseline, introduce one deliberate change, inspect the evidence, and explain the tradeoff. Include the downloadable report and the command needed to reproduce it. Prefer measured operational behavior over an unsupported claim of production readiness.

## Next extensions

Add one extension only after retaining a passing baseline: more realistic public workloads, an additional failure mode, stricter provenance, a larger evaluation set, or a runtime-version comparison. Preserve fixture/live distinctions and document negative results. The other four repositories in this portfolio can reuse the report schema without creating a runtime dependency on each other.
