# Public sources and provenance

| ID | Source | Terms | Use |
|---|---|---|---|
| otel-http | [OpenTelemetry HTTP metric conventions](https://github.com/open-telemetry/semantic-conventions) | Apache-2.0 | Compare instrumentation contracts with public semantic conventions |
| openmetrics | [OpenMetrics specification](https://github.com/prometheus/OpenMetrics) | Apache-2.0 | Reference for exposition parsing and metric types |
| container-releases | [Apple Container release metadata](https://github.com/apple/container/releases) | Public GitHub metadata; linked code Apache-2.0 | Attach runtime-version provenance and inspect release changes |
| pkl-releases | [Pkl release metadata](https://github.com/apple/pkl/releases) | Public GitHub metadata; linked code Apache-2.0 | Configuration-tool provenance |
| usgs-quakes | [USGS earthquakes, past day](https://earthquake.usgs.gov/earthquakes/feed/v1.0/geojson.php) | USGS public domain; verify third-party notices | Real public event records for sandbox analysis and replay inputs |
| nab-taxi | [NAB NYC taxi passenger time series](https://github.com/numenta/NAB) | NAB repository AGPL-3.0; upstream dataset attribution applies | Optional external time series for anomaly analysis; downloaded locally, not redistributed |
| nab-cpu | [NAB AWS EC2 CPU utilization](https://github.com/numenta/NAB) | NAB repository AGPL-3.0 | Compare anomaly detector behavior on public infrastructure telemetry |
| gsm8k | [GSM8K held-out math questions](https://github.com/openai/grade-school-math) | MIT | Real public inference prompts with exact numeric-answer evaluation |
| container-resources | [Apple Container resource documentation](https://github.com/apple/container/blob/main/docs/resource-usage.md) | Apache-2.0 | Ground interpretation of CPU, memory, and I/O metrics |
| prometheus-hardware | [Prometheus node exporter README](https://github.com/prometheus/node_exporter) | Apache-2.0 | Public reference for host telemetry and collector coverage |

The catalogue mixes real observations (USGS and NAB), evaluation questions (GSM8K), release metadata, and reference standards. Reference documents are not counted as measurement datasets. Built-in demo fixtures are authored synthetic data and labeled as such.

## Download behavior

Fetching requires clicking Fetch public source or calling the explicit CLI helper. URLs are allowlisted, HTTPS only, with no redirects, a 15 MB limit, and bounded timeouts. Each successful download writes the original bytes and a provenance record with URL, retrieval timestamp, length, and SHA-256 hash. Network failures produce errors instead of fabricated data.

Downloads are stored in ignored `artifacts/sources/` and are not republished in this repository. External data licenses remain applicable, particularly NAB's AGPL repository terms and upstream dataset notices. Inspect terms before redistributing modified data. GitHub metadata may include publicly authored user content; it is treated as untrusted data. The AI knowledge base contains short project-authored explanations with source links, not wholesale copies of third-party documentation.

## Actual data paths

USGS GeoJSON can be analyzed by the sandbox template. NAB CSV values can shape incident-simulation arrivals and feed runtime anomaly analysis. GSM8K questions and numeric answers can drive inference quality evaluation. OTel/OpenMetrics/Prometheus references support contract design; Apple/Pkl release metadata supports version provenance. Uploaded Prometheus exposition is checked by the telemetry gate.
