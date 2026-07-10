import os
import uvicorn
from fastapi import FastAPI
from mcp.server.fastmcp import FastMCP
from google.cloud import firestore
from google.cloud.firestore_v1.vector import Vector
from google.cloud.firestore_v1.base_vector_query import DistanceMeasure
from google import genai
from google.genai import types

# 1. Initialize Google Cloud project details
project_id = os.getenv("PROJECT_ID")
location = os.getenv("LOCATION", "us-central1")

if not project_id:
    raise RuntimeError("PROJECT_ID environment variable is required but not set.")

# 2. Initialize Firestore Client
db = firestore.Client(database="sre-genai")

# 3. Initialize the FastMCP Server
from mcp.server.transport_security import TransportSecuritySettings

mcp = FastMCP(
    "Catalog Search MCP Service",
    transport_security=TransportSecuritySettings(
        allowed_hosts=[
            "localhost",
            "localhost:*",
            "127.0.0.1",
            "127.0.0.1:*",
            "*.run.app"
        ]
    )
)

# 4. Tool 1: Text-based catalog search
@mcp.tool()
def search_catalog(query_text: str) -> str:
    """
    Search the Google Store tech and apparel catalog using a natural language text query.
    Performs a vector search on the text_embeddings field.
    """
    try:
        # Generate embedding for the query text using the Multimodal Embedding model (768 dimensions)
        # Load Gemini Embedding 2 model using google-genai client routed through Vertex AI 'us' multi-region
        client = genai.Client(vertexai=True, project=project_id, location="us")
        result = client.models.embed_content(
            model="gemini-embedding-2",
            contents=query_text,
            config=types.EmbedContentConfig(output_dimensionality=768)
        )
        query_vector = result.embeddings[0].values

        # Perform nearest-neighbor vector search in Firestore on the image_embeddings field
        collection = db.collection("products")
        vector_query = collection.find_nearest(
            vector_field="image_embeddings",
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
