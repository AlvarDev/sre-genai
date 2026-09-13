# SRE GenAI - Catalog MCP Microservice

FastMCP server exposing product catalog vector search tools over Server-Sent Events (SSE) protocol.

---

## 🛠️ Key Capabilities

* **Framework**: `FastMCP` mounted on FastAPI at `/mcp` (running on port 8001).
* **Database**: Cloud Firestore (Database ID: `sre-genai`, Collection: `products`).
* **Vector Index**: 768-dimensional `COSINE` distance nearest-neighbor vector search (`find_nearest`).
* **Telemetry**: OpenTelemetry SDK exporting to Google Cloud Trace with JSON structured logging and trace correlation.

---

## 🔌 Exposed MCP Tools

1. `search_catalog(query_text: str)`: Text query embedding generation & vector search.
2. `search_catalog_by_image(image_base64: str, mime_type: str = "image/jpeg")`: Decodes base64 image bytes, generates 768-dimensional multimodal embeddings using `gemini-embedding-2`, and executes nearest-neighbor vector search.

---

## 🏗️ Architecture

* `main.py`: `FastMCP` setup with DNS rebinding protection toggle, `ProductCatalogRepository` for Firestore vector operations, and tool registration.
* `Dockerfile`: Container image definition using `uv` and Python 3.11 slim base.
