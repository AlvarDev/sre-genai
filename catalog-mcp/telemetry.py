import json
import logging
import os
from datetime import datetime, timezone
from opentelemetry import trace
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.sdk.resources import Resource
from opentelemetry.exporter.cloud_trace import CloudTraceSpanExporter


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


def setup_logging(project_id: str):
    """Configures the root logger to output Google Cloud-compliant JSON logs."""
    log_handler = logging.StreamHandler()
    log_handler.setFormatter(CloudLoggingFormatter(gcp_project_id=project_id))
    root_logger = logging.getLogger()
    root_logger.setLevel(logging.INFO)
    root_logger.handlers.clear()
    root_logger.addHandler(log_handler)


def setup_telemetry(service_name: str, project_id: str) -> tuple[TracerProvider | None, trace.Tracer]:
    """Initializes OpenTelemetry TracerProvider with Google Cloud Trace exporter."""
    logger = logging.getLogger("catalog-mcp-server")
    tracer_provider = None
    try:
        resource = Resource.create({
            "service.name": service_name,
            "service.instance.id": os.getenv("HOSTNAME", "default-instance"),
        })
        trace_exporter = CloudTraceSpanExporter(project_id=project_id)
        tracer_provider = TracerProvider(resource=resource)
        tracer_provider.add_span_processor(BatchSpanProcessor(trace_exporter))
        trace.set_tracer_provider(tracer_provider)
        logger.info("OpenTelemetry Google Cloud Trace Exporter initialized in catalog-mcp.")
    except Exception as e:
        logger.warning(f"Failed to initialize CloudTraceSpanExporter in catalog-mcp: {e}")

    return tracer_provider, trace.get_tracer("catalog-mcp")


def flush_telemetry(tracer_provider: TracerProvider | None):
    """Flushes and shuts down the TracerProvider on application shutdown."""
    logger = logging.getLogger("catalog-mcp-server")
    if tracer_provider is not None:
        try:
            tracer_provider.force_flush()
            tracer_provider.shutdown()
            logger.info("Flushed OpenTelemetry traces on catalog-mcp shutdown.")
        except Exception as e:
            logger.error(f"Error flushing traces on catalog-mcp shutdown: {e}")
