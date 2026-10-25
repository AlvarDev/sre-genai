# SRE GenAI - Catalog MCP Microservice

FastMCP server exposing product catalog vector search tools over stateless Streamable HTTP (`/mcp/`).

---

## 🛠️ Key Capabilities

* **Framework**: `FastMCP` (stateless Streamable HTTP) mounted on FastAPI at `/mcp/` (running on port 8001).
* **Database**: Cloud Firestore (Database ID: `sre-genai`, Collection: `products`).
* **Vector Index**: 768-dimensional `COSINE` distance nearest-neighbor vector search (`find_nearest`).
* **Telemetry**: OpenTelemetry SDK exporting to Google Cloud Trace with JSON structured logging and trace correlation.

---

## 🔌 Exposed MCP Tools

1. `search_catalog(query_text: str)`: Text query embedding generation & vector search.
2. `search_catalog_by_image(image_base64: str, mime_type: str = "image/jpeg")`: Decodes base64 image bytes, generates 768-dimensional multimodal embeddings using `gemini-embedding-2`, and executes nearest-neighbor vector search.

---

## 🏗️ Architecture

* `main.py`: `FastMCP` stateless Streamable HTTP setup with DNS rebinding protection toggle, lifespan session manager, and tool registration.
* `catalog_service.py`: Async text and multimodal embedding + Firestore vector search orchestration.
* `repository.py`: `ProductCatalogRepository` using Firestore `AsyncClient` for nearest-neighbor vector queries.
* `Dockerfile`: Multi-stage container image built with `uv` (Python 3.13) on a Google Distroless (`gcr.io/distroless/python3-debian13:nonroot`) runtime.
