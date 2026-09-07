import json
import logging
import os
from datetime import datetime, timezone
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import firebase_admin
from firebase_admin import credentials, firestore
from google.cloud import firestore as gcloud_firestore

from opentelemetry import metrics
from opentelemetry import trace
from opentelemetry.sdk.metrics import MeterProvider
from opentelemetry.sdk.metrics.export import PeriodicExportingMetricReader
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.sdk.resources import Resource
from opentelemetry.exporter.cloud_monitoring import CloudMonitoringMetricsExporter
from opentelemetry.exporter.cloud_trace import CloudTraceSpanExporter
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor

provider = None
tracer_provider = None
project_id = os.getenv("PROJECT_ID")


class CloudLoggingFormatter(logging.Formatter):
    """
    Formats log records as JSON conforming to Google Cloud Logging specification.
    Injects logging.googleapis.com/trace and logging.googleapis.com/spanId from
    the active OpenTelemetry span context for automatic log correlation.
    """
    def __init__(self, gcp_project_id: str | None = None):
        super().__init__()
        self.project_id = gcp_project_id or ""

    def format(self, record: logging.LogRecord) -> str:
        log_entry = {
            "timestamp": datetime.fromtimestamp(record.created, tz=timezone.utc).isoformat(),
            "severity": record.levelname,
            "message": record.getMessage(),
            "logger": record.name,
        }
        
        current_span = trace.get_current_span()
        if current_span and current_span.is_recording():
            ctx = current_span.get_span_context()
            trace_id_hex = format(ctx.trace_id, "032x")
            span_id_hex = format(ctx.span_id, "016x")
            if self.project_id:
                log_entry["logging.googleapis.com/trace"] = f"projects/{self.project_id}/traces/{trace_id_hex}"
            else:
                log_entry["logging.googleapis.com/trace"] = trace_id_hex
            log_entry["logging.googleapis.com/spanId"] = span_id_hex
            log_entry["logging.googleapis.com/trace_sampled"] = ctx.trace_flags.sampled

        if record.exc_info:
            log_entry["exception"] = self.formatException(record.exc_info)

        return json.dumps(log_entry)


def setup_logging():
    handler = logging.StreamHandler()
    handler.setFormatter(CloudLoggingFormatter(gcp_project_id=project_id))
    root_logger = logging.getLogger()
    root_logger.setLevel(logging.INFO)
    root_logger.handlers.clear()
    root_logger.addHandler(handler)


try:
    export_interval_ms = int(os.getenv("OTEL_EXPORT_INTERVAL_MS", "60000"))
    service_name = os.getenv("SERVICE_NAME", os.getenv("K_SERVICE", "backend-service"))
    instance_id = os.getenv("HOSTNAME", "default-instance")
    resource = Resource.create({
        "service.name": service_name,
        "service.instance.id": instance_id,
    })
    exporter = CloudMonitoringMetricsExporter(project_id=project_id)
    reader = PeriodicExportingMetricReader(exporter, export_interval_millis=export_interval_ms)
    provider = MeterProvider(metric_readers=[reader], resource=resource)
    metrics.set_meter_provider(provider)
    print(f"OpenTelemetry Google Cloud Metrics Exporter initialized (Export Interval: {export_interval_ms}ms).")

    trace_exporter = CloudTraceSpanExporter(project_id=project_id)
    tracer_provider = TracerProvider(resource=resource)
    tracer_provider.add_span_processor(BatchSpanProcessor(trace_exporter))
    trace.set_tracer_provider(tracer_provider)
    print("OpenTelemetry Google Cloud Trace Exporter initialized.")
except Exception as e:
    print(f"Failed to initialize OpenTelemetry Google Cloud Exporters: {e}")

setup_logging()

if not firebase_admin._apps:
    firebase_admin.initialize_app()

database_id = os.getenv("FIRESTORE_DATABASE")
if not database_id:
    raise RuntimeError("FIRESTORE_DATABASE environment variable is required but not set.")

db = gcloud_firestore.Client(database=database_id)

@asynccontextmanager
async def lifespan(app: FastAPI):
    yield
    if provider is not None:
        try:
            provider.force_flush()
            provider.shutdown()
            print("Flushed OpenTelemetry metrics on app shutdown.")
        except Exception as e:
            print(f"Error flushing metrics: {e}")
    if tracer_provider is not None:
        try:
            tracer_provider.force_flush()
            tracer_provider.shutdown()
            print("Flushed OpenTelemetry traces on app shutdown.")
        except Exception as e:
            print(f"Error flushing traces: {e}")

def setup_cors(app: FastAPI):
    allowed_origins_env = os.getenv("ALLOWED_ORIGINS", "*")
    allowed_origins = [origin.strip() for origin in allowed_origins_env.split(",") if origin.strip()]
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=False,
        allow_methods=["*"],
        allow_headers=["*"],
    )

def setup_telemetry(app: FastAPI):
    FastAPIInstrumentor.instrument_app(app)
