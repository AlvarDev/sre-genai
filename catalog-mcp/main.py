import base64
import json
import os
import uvicorn
import logging
from datetime import datetime, timezone
from contextlib import asynccontextmanager
from fastapi import FastAPI
from mcp.server.fastmcp import FastMCP
from google.cloud import firestore
from google.cloud.firestore_v1.vector import Vector
from google.cloud.firestore_v1.base_vector_query import DistanceMeasure
from google import genai
from google.genai import types

from opentelemetry import trace
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.sdk.resources import Resource
from opentelemetry.exporter.cloud_trace import CloudTraceSpanExporter
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor

# 1. Initialize Google Cloud project details
project_id = os.getenv("PROJECT_ID")
location = os.getenv("LOCATION")
database_id = os.getenv("FIRESTORE_DATABASE")

if not project_id:
    raise RuntimeError("PROJECT_ID environment variable is required but not set.")
if not location:
    raise RuntimeError("LOCATION environment variable is required but not set.")
if not database_id:
    raise RuntimeError("FIRESTORE_DATABASE environment variable is required but not set.")


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


log_handler = logging.StreamHandler()
log_handler.setFormatter(CloudLoggingFormatter(gcp_project_id=project_id))
root_logger = logging.getLogger()
root_logger.setLevel(logging.INFO)
root_logger.handlers.clear()
root_logger.addHandler(log_handler)

logger = logging.getLogger("catalog-mcp-server")



class ProductCatalogRepository:
    """
    Handles data access to the Firestore products catalog.
    Encapsulates vector search queries and string formatting for LLM consumption.
    """
    def __init__(self, firestore_db):
        self.db = firestore_db
        self.collection = firestore_db.collection("products")

    def find_similar_products(self, vector: list[float], limit: int = 3) -> list[dict]:
        """
        Executes a nearest-neighbor vector search in Firestore and returns raw dicts.
        """
        vector_query = self.collection.find_nearest(
            vector_field="image_embeddings",
            query_vector=Vector(vector),
            distance_measure=DistanceMeasure.COSINE,
            limit=limit
        )
        return [doc.to_dict() for doc in vector_query.stream()]

    @staticmethod
    def format_products_to_string(products: list[dict]) -> str:
        """
        Formats a list of product records into a clean string representation for the LLM.
        """
        if not products:
            return "No matching products found in the catalog."
            
        formatted = []
        for data in products:
            product_info = (
                f"Title: {data.get('title')}\n"
                f"SKU: {data.get('parent_sku')}\n"
                f"Price: R$ {data.get('retail_price')}\n"
                f"Description: {data.get('shortdesc')}\n"
                f"Image URL: {data.get('img_url')}\n"
            )
            formatted.append(product_info)
        return "\n---\n".join(formatted)


# 2. Initialize Clients and Repositories Globally
db = firestore.Client(database=database_id)
catalog_repo = ProductCatalogRepository(db)
genai_client = genai.Client(vertexai=True, project=project_id, location=location)
logger.info(f"Initialized Firestore and GenAI clients. Project: {project_id}")

# 3. Initialize OpenTelemetry Tracer
tracer_provider = None
try:
    resource = Resource.create({
        "service.name": os.getenv("SERVICE_NAME", os.getenv("K_SERVICE", "catalog-mcp")),
        "service.instance.id": os.getenv("HOSTNAME", "default-instance"),
    })
    trace_exporter = CloudTraceSpanExporter(project_id=project_id)
    tracer_provider = TracerProvider(resource=resource)
    tracer_provider.add_span_processor(BatchSpanProcessor(trace_exporter))
    trace.set_tracer_provider(tracer_provider)
    logger.info("OpenTelemetry Google Cloud Trace Exporter initialized in catalog-mcp.")
except Exception as e:
    logger.warning(f"Failed to initialize CloudTraceSpanExporter in catalog-mcp: {e}")

tracer = trace.get_tracer("catalog-mcp")

# 4. Initialize the FastMCP Server
from mcp.server.transport_security import TransportSecuritySettings

# Check if running in a containerized prod environment (Cloud Run sets K_SERVICE, Kubernetes sets KUBERNETES_SERVICE_HOST)
is_prod = (os.getenv("K_SERVICE") is not None) or (os.getenv("KUBERNETES_SERVICE_HOST") is not None)

mcp = FastMCP(
    "Catalog Search MCP Service",
    transport_security=TransportSecuritySettings(
        enable_dns_rebinding_protection=not is_prod
    )
)
logger.info(f"Initialized FastMCP server. DNS Rebinding protection: {not is_prod}")

# 5. Tool 1: Text-based catalog search
@mcp.tool()
def search_catalog(query_text: str) -> str:
    """
    Search the Google Store tech and apparel catalog using a natural language text query.
    Performs a nearest-neighbor vector search on the image_embeddings field in Firestore.
    """
    with tracer.start_as_current_span("mcp.tool.search_catalog") as span:
        span.set_attribute("catalog.query_text", query_text)
        try:
            logger.info(f"Executing catalog text search for query: '{query_text}'")
            
            # Generate embedding for the query text using the Multimodal Embedding model (768 dimensions)
            result = genai_client.models.embed_content(
                model="gemini-embedding-2",
                contents=query_text,
                config=types.EmbedContentConfig(output_dimensionality=768)
            )
            query_vector = result.embeddings[0].values

            # Perform search and format using Repository pattern
            products = catalog_repo.find_similar_products(query_vector)
            span.set_attribute("catalog.results_count", len(products))
            formatted_result = catalog_repo.format_products_to_string(products)
            
            logger.info(f"Text search complete. Found {len(products)} products.")
            return formatted_result

        except Exception as e:
            logger.error(f"Error executing catalog search: {str(e)}", exc_info=True)
            return f"Error executing catalog search: {str(e)}"

# 6. Tool 2: Image-based catalog search (Visual Search)
@mcp.tool()
def search_catalog_by_image(image_base64: str, mime_type: str = "image/jpeg") -> str:
    """
    Search the Google Store catalog using an uploaded image.
    Generates a multimodal embedding vector using gemini-embedding-2 and performs
    nearest-neighbor vector search on the image_embeddings field in Firestore.
    """
    with tracer.start_as_current_span("mcp.tool.search_catalog_by_image") as span:
        span.set_attribute("catalog.mime_type", mime_type)
        try:
            logger.info("Executing visual catalog search with base64 image payload.")
            image_bytes = base64.b64decode(image_base64)

            # Generate embedding for the image using the Multimodal Embedding model (768 dimensions)
            result = genai_client.models.embed_content(
                model="gemini-embedding-2",
                contents=[
                    types.Part.from_bytes(
                        data=image_bytes,
                        mime_type=mime_type
                    )
                ],
                config=types.EmbedContentConfig(output_dimensionality=768)
            )
            image_vector = result.embeddings[0].values
            
            # Perform search and format using Repository pattern
            products = catalog_repo.find_similar_products(image_vector)
            span.set_attribute("catalog.results_count", len(products))
            formatted_result = catalog_repo.format_products_to_string(products)
            
            logger.info(f"Visual search complete. Found {len(products)} products.")
            return formatted_result

        except Exception as e:
            logger.error(f"Error executing visual search: {str(e)}", exc_info=True)
            return f"Error executing visual search: {str(e)}"

# 7. Lifespan and Mount the MCP SSE application onto FastAPI
@asynccontextmanager
async def lifespan(app: FastAPI):
    yield
    if tracer_provider is not None:
        try:
            tracer_provider.force_flush()
            tracer_provider.shutdown()
            logger.info("Flushed OpenTelemetry traces on catalog-mcp shutdown.")
        except Exception as e:
            logger.error(f"Error flushing traces on catalog-mcp shutdown: {e}")

app = FastAPI(title="Catalog MCP Server API", lifespan=lifespan)

@app.get("/health")
def health():
    return {"status": "healthy", "service": "catalog-mcp"}

app.mount("/mcp", mcp.sse_app())
FastAPIInstrumentor.instrument_app(app)

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8001)
