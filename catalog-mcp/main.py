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
from google.genai import types
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor

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
db = firestore.Client(database=database_id)
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
    flush_telemetry(tracer_provider)

app = FastAPI(title="Catalog MCP Server API", lifespan=lifespan)

@app.get("/health")
def health():
    return {"status": "healthy", "service": "catalog-mcp"}

app.mount("/mcp", mcp.sse_app())
FastAPIInstrumentor.instrument_app(app)

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8001)
