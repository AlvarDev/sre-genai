import os
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import firebase_admin
from firebase_admin import credentials, firestore
from google.cloud import firestore as gcloud_firestore

from opentelemetry import metrics
from opentelemetry.sdk.metrics import MeterProvider
from opentelemetry.sdk.metrics.export import PeriodicExportingMetricReader
from opentelemetry.exporter.cloud_monitoring import CloudMonitoringMetricsExporter
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor

provider = None

try:
    export_interval_ms = int(os.getenv("OTEL_EXPORT_INTERVAL_MS", "60000"))
    exporter = CloudMonitoringMetricsExporter(project_id=os.getenv("PROJECT_ID"))
    reader = PeriodicExportingMetricReader(exporter, export_interval_millis=export_interval_ms)
    provider = MeterProvider(metric_readers=[reader])
    metrics.set_meter_provider(provider)
    print(f"OpenTelemetry Google Cloud Metrics Exporter initialized (Export Interval: {export_interval_ms}ms).")
except Exception as e:
    print(f"Failed to initialize OpenTelemetry Google Cloud Metrics Exporter: {e}")

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
            print(f"Error flushing telemetry: {e}")

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
