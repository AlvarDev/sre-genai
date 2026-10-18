import base64
import os
import uvicorn
import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI
from mcp.server.fastmcp import FastMCP
from mcp.server.transport_security import TransportSecuritySettings
from google.cloud import firestore
from google import genai
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor

import catalog_service
from telemetry import setup_logging, setup_telemetry, flush_telemetry
from repository import ProductCatalogRepository

# 1. Initialize Google Cloud project details
project_id = os.getenv("PROJECT_ID")
gemini_location = os.getenv("GEMINI_LOCATION")
database_id = os.getenv("FIRESTORE_DATABASE")

if not project_id:
    raise RuntimeError("PROJECT_ID environment variable is required but not set.")
if not gemini_location:
    raise RuntimeError("GEMINI_LOCATION environment variable is required but not set.")
if not database_id:
    raise RuntimeError("FIRESTORE_DATABASE environment variable is required but not set.")

# Configure structured logging
setup_logging(project_id=project_id)
logger = logging.getLogger("catalog-mcp-server")

# 2. Initialize Clients and Repositories Globally
db = firestore.AsyncClient(database=database_id)
catalog_repo = ProductCatalogRepository(db)
genai_client = genai.Client(vertexai=True, project=project_id, location=gemini_location)
logger.info(f"Initialized Firestore and GenAI clients. Project: {project_id}")

service_name = os.getenv("K_SERVICE") or os.getenv("SERVICE_NAME")
if not service_name:
    raise RuntimeError("Missing required service name: set K_SERVICE or SERVICE_NAME.")

# 3. Initialize OpenTelemetry Tracer
tracer_provider, tracer = setup_telemetry(service_name=service_name, project_id=project_id)

# 4. Initialize the FastMCP Server
# Check if running in a containerized prod environment (Cloud Run sets K_SERVICE, Kubernetes sets KUBERNETES_SERVICE_HOST)
is_prod = (os.getenv("K_SERVICE") is not None) or (os.getenv("KUBERNETES_SERVICE_HOST") is not None)

if is_prod:
    # Behind Cloud Run / Kubernetes the Host header is the service DNS name. On Cloud Run,
    # access is enforced by IAM (OIDC); in the local cluster the Service is in-cluster only.
    transport_security = TransportSecuritySettings(enable_dns_rebinding_protection=False)
else:
    transport_security = TransportSecuritySettings(
        enable_dns_rebinding_protection=True,
        allowed_hosts=["localhost:*", "127.0.0.1:*"],
    )

# Stateless Streamable HTTP: every request is independent, so any instance can serve it
# (SSE sessions are pinned to one instance and break when Cloud Run scales out).
mcp = FastMCP(
    "Catalog Search MCP Service",
    stateless_http=True,
    json_response=True,
    streamable_http_path="/",
    transport_security=transport_security,
)
logger.info("Initialized FastMCP server. DNS Rebinding protection: %s", not is_prod)

# Returned to the calling agent on failure; details stay in logs/traces only.
TOOL_ERROR_MESSAGE = "Erro ao consultar o catálogo."

# 5. Tool 1: Text-based catalog search
@mcp.tool()
async def search_catalog(query_text: str) -> str:
    """
    Search the Google Store tech and apparel catalog using a natural language text query.
    Performs a nearest-neighbor vector search on the image_embeddings field in Firestore.
    """
    with tracer.start_as_current_span("mcp.tool.search_catalog") as span:
        span.set_attribute("catalog.query_text", query_text)
        try:
            logger.info("Executing catalog text search for query: '%s'", query_text)
            formatted_result, count = await catalog_service.search_by_text(
                genai_client, catalog_repo, query_text
            )
            span.set_attribute("catalog.results_count", count)
            logger.info("Text search complete. Found %d products.", count)
            return formatted_result

        except Exception as e:
            span.record_exception(e)
            logger.exception("Error executing catalog search")
            return TOOL_ERROR_MESSAGE

# 6. Tool 2: Image-based catalog search (Visual Search)
@mcp.tool()
async def search_catalog_by_image(image_base64: str, mime_type: str = "image/jpeg") -> str:
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
            formatted_result, count = await catalog_service.search_by_image(
                genai_client, catalog_repo, image_bytes, mime_type
            )
            span.set_attribute("catalog.results_count", count)
            logger.info("Visual search complete. Found %d products.", count)
            return formatted_result

        except Exception as e:
            span.record_exception(e)
            logger.exception("Error executing visual search")
            return TOOL_ERROR_MESSAGE

# 7. Lifespan and Mount the MCP Streamable HTTP application onto FastAPI
@asynccontextmanager
async def lifespan(app: FastAPI):
    # The Streamable HTTP session manager must run for the lifetime of the app.
    async with mcp.session_manager.run():
        yield
    flush_telemetry(tracer_provider)

app = FastAPI(title="Catalog MCP Server API", lifespan=lifespan)

@app.get("/health")
def health():
    return {"status": "healthy", "service": "catalog-mcp"}

# Endpoint: /mcp/ (streamable_http_path="/" inside the /mcp mount)
app.mount("/mcp", mcp.streamable_http_app())
FastAPIInstrumentor.instrument_app(app, exclude_spans=["receive", "send"])

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8001)
