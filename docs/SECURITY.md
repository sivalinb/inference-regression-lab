# Security and limitations

Small sample p95 values are descriptive; repeat at least 100 requests before making tail claims and report uncertainty. Client timing includes network overhead. A declared model name is not cryptographic proof of server identity. Cancellation closes the client stream but does not prove backend GPU/CPU reclamation. The CPU model runner uses an OCI image and read-only model mount; GPU passthrough is not required. Only the selected GGUF file is copied into a temporary staging directory and exposed read-only. Staging is removed when the managed server is stopped. Runtime images should be pinned by digest for formal benchmarks.

## Shared boundaries

The app is intended for a trusted local user. It has no multi-user authentication or tenant isolation at the Streamlit layer. Public deployment requires a separate access-control and execution-service design. The Pkl evaluator only loads the repository's trusted module. Public sources are allowlisted and not executed. Input sizes, resource settings, subprocess output, and execution durations are bounded where implemented. The detailed report distinguishes active enforcement from documentation and experimental assumptions.

Source and model content may include misleading instructions; retrieval and model outputs have no authority to change application policy. Citation membership alone does not prove correctness. Never publish private production logs or credentials as example data. Report suspected security defects privately through the repository owner's GitHub contact channels; do not include working credentials in an issue.
