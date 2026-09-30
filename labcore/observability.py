"""Local JSONL audit trail, Prometheus exposition, optional OTLP traces."""
from contextlib import contextmanager
import hashlib
import json
import os
from pathlib import Path
import threading
import time
import uuid
from prometheus_client import CollectorRegistry, Counter, Histogram, generate_latest
from opentelemetry.sdk.resources import Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.trace import Status, StatusCode


class Recorder:
    def __init__(self, root: Path, service: str):
        self.root = root / "artifacts"
        self.root.mkdir(exist_ok=True)
        self.lock = threading.Lock()
        self.registry = CollectorRegistry()
        self.count = Counter("lab_operations_total", "Completed lab operations", ["operation", "status"], registry=self.registry)
        self.latency = Histogram("lab_operation_seconds", "Operation duration", ["operation"], registry=self.registry)
        self.provider = TracerProvider(resource=Resource.create({"service.name": service}))
        endpoint = os.environ.get("OTEL_EXPORTER_OTLP_ENDPOINT")
        if endpoint:
            from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter
            self.provider.add_span_processor(BatchSpanProcessor(OTLPSpanExporter(endpoint=endpoint.rstrip("/") + "/v1/traces")))
        self.tracer = self.provider.get_tracer(service)

    @contextmanager
    def span(self, operation, **attributes):
        start = time.monotonic()
        status = "ok"
        run_id = uuid.uuid4().hex
        with self.tracer.start_as_current_span(operation, attributes={"run.id": run_id}, record_exception=False, set_status_on_exception=False) as span:
            try:
                yield run_id
            except Exception as e:
                status = "error"
                # No exception message: it may contain user inputs or credentials.
                span.set_attribute("error.type", type(e).__name__)
                span.set_status(Status(StatusCode.ERROR))
                raise
            finally:
                elapsed = time.monotonic() - start
                event = {"time_unix": time.time(), "run_id": run_id, "operation": operation,
                         "status": status, "duration_s": elapsed,
                         "trace_id": f"{span.get_span_context().trace_id:032x}"}
                event.update({k: v for k, v in attributes.items() if k in {"mode", "case", "source_id"}})
                with self.lock:
                    with (self.root / "events.jsonl").open("a") as f:
                        f.write(json.dumps(event) + "\n")
                    self.count.labels(operation, status).inc()
                    self.latency.labels(operation).observe(elapsed)
                    (self.root / "metrics.prom").write_bytes(generate_latest(self.registry))

    def save(self, report, name="report"):
        data = json.dumps(report, indent=2, allow_nan=False).encode()
        target = self.root / f"{name}-{uuid.uuid4().hex[:12]}.json"
        target.write_bytes(data)
        return {"path": str(target), "sha256": hashlib.sha256(data).hexdigest()}
