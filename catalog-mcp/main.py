import os
import uvicorn
from fastapi import FastAPI
from mcp.server.fastmcp import FastMCP
from google.cloud import firestore
from google.cloud.firestore_v1.vector import Vector
from google.cloud.firestore_v1.base_vector_query import DistanceMeasure
import vertexai
from vertexai.language_models import TextEmbeddingModel

# 1. Initialize Google Cloud project details
project_id = os.getenv("PROJECT_ID", "sre-genai")
location = os.getenv("LOCATION", "us-central1")

# Initialize Vertex AI for generating text query embeddings
if os.getenv("LOCAL_DEVELOPMENT") != "true":
    vertexai.init(project=project_id, location=location)

# 2. Initialize Firestore Client
# The Firestore library automatically detects FIRESTORE_EMULATOR_HOST if set in dev.
# We explicitly target the named database 'sre-genai'.
db = firestore.Client(database="sre-genai")

# 3. Initialize the FastMCP Server
mcp = FastMCP("Catalog Search MCP Service")

# 4. Tool 1: Text-based catalog search
@mcp.tool()
def search_catalog(query_text: str) -> str:
    """
    Search the Google Store tech and apparel catalog using a natural language text query.
    Performs a vector search on the text_embeddings field.
    """
    try:
        # Generate embedding for the query text
        if os.getenv("LOCAL_DEVELOPMENT") == "true" and not os.getenv("GOOGLE_APPLICATION_CREDENTIALS"):
            # Dummy vector for offline local testing
            query_vector = [0.1] * 768
        else:
            # Load text embedding model
            model = TextEmbeddingModel.from_pretrained("text-embedding-004")
            embeddings = model.get_embeddings([query_text])
            query_vector = embeddings[0].values

        # Perform nearest-neighbor vector search in Firestore
        collection = db.collection("products")
        vector_query = collection.find_nearest(
            vector_field="text_embeddings",
            query_vector=Vector(query_vector),
            distance_measure=DistanceMeasure.COSINE,
            limit=3
        )
        docs = vector_query.stream()

        # Format results
        products = []
        for doc in docs:
            data = doc.to_dict()
            product_info = (
                f"Title: {data.get('title')}\n"
                f"SKU: {data.get('parent_sku')}\n"
                f"Price: R$ {data.get('retail_price')}\n"
                f"Description: {data.get('shortdesc')}\n"
                f"Image URL: {data.get('img_url')}\n"
            )
            products.append(product_info)

        if not products:
            return "No matching products found in the catalog."

        return "\n---\n".join(products)

    except Exception as e:
        return f"Error executing catalog search: {str(e)}"

# 5. Tool 2: Image-based catalog search (Visual Search)
@mcp.tool()
def search_catalog_by_image(image_vector: list[float]) -> str:
    """
    Search the Google Store catalog using a multimodal image embedding vector.
    Performs nearest-neighbor search on the image_embeddings field in Firestore.
    """
    try:
        # Perform nearest-neighbor vector search in Firestore
        collection = db.collection("products")
        vector_query = collection.find_nearest(
            vector_field="image_embeddings",
            query_vector=Vector(image_vector),
            distance_measure=DistanceMeasure.COSINE,
            limit=3
        )
        docs = vector_query.stream()

        # Format results
        products = []
        for doc in docs:
            data = doc.to_dict()
            product_info = (
                f"Title: {data.get('title')}\n"
                f"SKU: {data.get('parent_sku')}\n"
                f"Price: R$ {data.get('retail_price')}\n"
                f"Description: {data.get('shortdesc')}\n"
                f"Image URL: {data.get('img_url')}\n"
            )
            products.append(product_info)

        if not products:
            return "No visually matching products found in the catalog."

        return "\n---\n".join(products)

    except Exception as e:
        return f"Error executing visual search: {str(e)}"

# 6. Mount the MCP SSE application onto FastAPI
app = FastAPI(title="Catalog MCP Server API")
app.mount("/mcp", mcp.sse_app())

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8001)
