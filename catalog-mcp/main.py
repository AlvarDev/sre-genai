import os
import uvicorn
import logging
from fastapi import FastAPI
from mcp.server.fastmcp import FastMCP
from google.cloud import firestore
from google.cloud.firestore_v1.vector import Vector
from google.cloud.firestore_v1.base_vector_query import DistanceMeasure
from google import genai
from google.genai import types

# Configure structured logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
logger = logging.getLogger("catalog-mcp-server")

# 1. Initialize Google Cloud project details
project_id = os.getenv("PROJECT_ID")
location = os.getenv("LOCATION", "us-central1")

if not project_id:
    raise RuntimeError("PROJECT_ID environment variable is required but not set.")


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
db = firestore.Client(database="sre-genai")
catalog_repo = ProductCatalogRepository(db)
genai_client = genai.Client(vertexai=True, project=project_id, location="us")
logger.info(f"Initialized Firestore and GenAI clients. Project: {project_id}")

# 3. Initialize the FastMCP Server
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

# 4. Tool 1: Text-based catalog search
@mcp.tool()
def search_catalog(query_text: str) -> str:
    """
    Search the Google Store tech and apparel catalog using a natural language text query.
    Performs a nearest-neighbor vector search on the image_embeddings field in Firestore.
    """
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
        formatted_result = catalog_repo.format_products_to_string(products)
        
        logger.info(f"Text search complete. Found {len(products)} products.")
        return formatted_result

    except Exception as e:
        logger.error(f"Error executing catalog search: {str(e)}", exc_info=True)
        return f"Error executing catalog search: {str(e)}"

# 5. Tool 2: Image-based catalog search (Visual Search)
@mcp.tool()
def search_catalog_by_image(image_vector: list[float]) -> str:
    """
    Search the Google Store catalog using a multimodal image embedding vector.
    Performs nearest-neighbor vector search on the image_embeddings field in Firestore.
    """
    try:
        logger.info(f"Executing visual catalog search with vector dimension: {len(image_vector)}")
        
        # Perform search and format using Repository pattern
        products = catalog_repo.find_similar_products(image_vector)
        formatted_result = catalog_repo.format_products_to_string(products)
        
        logger.info(f"Visual search complete. Found {len(products)} products.")
        return formatted_result

    except Exception as e:
        logger.error(f"Error executing visual search: {str(e)}", exc_info=True)
        return f"Error executing visual search: {str(e)}"

# 6. Mount the MCP SSE application onto FastAPI
app = FastAPI(title="Catalog MCP Server API")
app.mount("/mcp", mcp.sse_app())

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8001)
