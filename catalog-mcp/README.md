# SRE GenAI - Catalog MCP Microservice

FastMCP server exposing product catalog vector search tools over Server-Sent Events (SSE) protocol.

---

## 🛠️ Key Capabilities

* **Framework**: `FastMCP` mounted on FastAPI at `/mcp` (running on port 8001).
* **Database**: Cloud Firestore (Database ID: `sre-genai`, Collection: `products`).
* **Vector Index**: 768-dimensional `COSINE` distance nearest-neighbor vector search (`find_nearest`).

---

## 🔌 Exposed MCP Tools

1. `search_catalog(query_text: str)`: Text query embedding generation & vector search.
2. `search_catalog_by_image(image_vector: list[float])`: Image vector nearest-neighbor search.

---

## 🏗️ Architecture

* `main.py`: `FastMCP` setup with DNS rebinding protection toggle, `ProductCatalogRepository` for Firestore vector operations, and tool registration.
* `Dockerfile`: Container image definition using `uv` and Python 3.11 slim base.
