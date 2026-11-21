# Catalog MCP Server (`catalog-mcp`)

## Overview

`catalog-mcp` (`sre-genai-catalog-mcp` in [`pyproject.toml`](./pyproject.toml)) is a stateless Python Model Context Protocol (MCP) server built with FastAPI and FastMCP (`mcp.server.fastmcp.FastMCP`) over Streamable HTTP. It exposes text and image multimodal product search tools backed by Vertex AI `gemini-embedding-2` vector generation ([`catalog_service.py`](./catalog_service.py)) and Google Cloud Firestore nearest-neighbor vector search ([`repository.py`](./repository.py)), instrumented with OpenTelemetry Cloud Trace export and trace-correlated structured JSON logging ([`telemetry.py`](./telemetry.py)).

## Interface

- [`pyproject.toml`](./pyproject.toml) `[project]`: Python package `sre-genai-catalog-mcp` (`0.1.0`, `requires-python = ">=3.11"`).
- [`main.py`](./main.py) `[main.py:app]`: FastAPI ASGI application (`"Catalog MCP Server API"`) mounting `mcp.streamable_http_app()` at `/mcp` and instrumented with `FastAPIInstrumentor` (excluding `"receive"` and `"send"` spans).
- [`main.py`](./main.py) `[main.py:health]`: `GET /health` endpoint returning `{"status": "healthy", "service": "catalog-mcp"}`.
- [`main.py`](./main.py) `[main.py:mcp]`: `FastMCP("Catalog Search MCP Service")` instance configured with `stateless_http=True`, `json_response=True`, and `streamable_http_path="/"`.
- [`main.py`](./main.py) `[main.py:search_catalog]`: `@mcp.tool() async def search_catalog(query_text: str) -> str` — natural-language catalog search tool.
- [`main.py`](./main.py) `[main.py:search_catalog_by_image]`: `@mcp.tool() async def search_catalog_by_image(image_base64: str, mime_type: str = "image/jpeg") -> str` — base64 image visual catalog search tool.
- [`main.py`](./main.py) `[main.py:TOOL_ERROR_MESSAGE]`: Fallback error string (`"Erro ao consultar o catálogo."`) returned to MCP callers when tool execution raises an exception.
- [`main.py`](./main.py) `[main.py:lifespan]`: FastAPI `asynccontextmanager` running `mcp.session_manager.run()` across application startup/shutdown and invoking `flush_telemetry(tracer_provider)` on exit.
- [`catalog_service.py`](./catalog_service.py) `[catalog_service.py:EMBEDDING_MODEL]`, `[catalog_service.py:EMBEDDING_DIM]`: Embedding configuration constants (`"gemini-embedding-2"`, `768`).
- [`catalog_service.py`](./catalog_service.py) `[catalog_service.py:search_by_text]`: `async def search_by_text(genai_client, repo, query_text: str) -> tuple[str, int]` — embeds text query and returns `(formatted_products, count)`.
- [`catalog_service.py`](./catalog_service.py) `[catalog_service.py:search_by_image]`: `async def search_by_image(genai_client, repo, image_bytes: bytes, mime_type: str) -> tuple[str, int]` — embeds raw image bytes and returns `(formatted_products, count)`.
- [`repository.py`](./repository.py) `[repository.py:ProductCatalogRepository]`: Firestore data-access repository bound to the `"products"` collection:
  - `[repository.py:ProductCatalogRepository.find_similar_products]`: `async def find_similar_products(self, vector: list[float], limit: int = 3) -> list[dict]`
  - `[repository.py:ProductCatalogRepository.format_products_to_string]`: `@staticmethod def format_products_to_string(products: list[dict]) -> str`
- [`telemetry.py`](./telemetry.py) `[telemetry.py:FLUSH_TIMEOUT_MILLIS]`: Shutdown trace flush timeout constant (`3000` ms).
- [`telemetry.py`](./telemetry.py) `[telemetry.py:CloudLoggingFormatter]`: `logging.Formatter` emitting Google Cloud Logging JSON entries correlated with active OpenTelemetry trace/span IDs.
- [`telemetry.py`](./telemetry.py) `[telemetry.py:setup_logging]`, `[telemetry.py:build_instance_id]`, `[telemetry.py:setup_telemetry]`, `[telemetry.py:flush_telemetry]`: Structured logging and OpenTelemetry lifecycle helpers.
- [`Dockerfile`](./Dockerfile) `[Dockerfile:EXPOSE]`, `[Dockerfile:ENTRYPOINT]`: Multi-stage distroless container serving `uvicorn main:app --host 0.0.0.0 --port 8001`.
- [`cloudbuild.yaml`](./cloudbuild.yaml) `[cloudbuild.yaml:deploy-catalog-mcp]`: Cloud Build pipeline deploying Cloud Run service `catalog-mcp-server` in `southamerica-east1` on port `8001`.
- Subdirectories: None (no child code packages; `tests/` contains unit tests only).

## Invariants

- `[main.py:project_id]`, `[main.py:gemini_location]`, `[main.py:database_id]`, `[main.py:service_name]`: Importing `main.py` raises `RuntimeError` immediately unless `PROJECT_ID`, `GEMINI_LOCATION`, `FIRESTORE_DATABASE`, and at least one of `K_SERVICE` or `SERVICE_NAME` are set and non-empty.
- `[main.py:is_prod]`, `[main.py:transport_security]`: DNS rebinding protection is disabled (`enable_dns_rebinding_protection=False`) when `K_SERVICE` or `KUBERNETES_SERVICE_HOST` is set, and enabled with `allowed_hosts=["localhost:*", "127.0.0.1:*"]` in local environments.
- `[main.py:mcp]`, `[main.py:lifespan]`: MCP transport runs in stateless Streamable HTTP mode (`stateless_http=True`, `json_response=True`); `mcp.session_manager.run()` must remain active for the duration of the FastAPI lifespan.
- `[main.py:search_catalog]`, `[main.py:search_catalog_by_image]`: Unhandled exceptions inside MCP tool handlers are never propagated to callers; exceptions are recorded on the active OpenTelemetry span, logged via `logger.exception`, and replaced with `TOOL_ERROR_MESSAGE`.
- `[catalog_service.py:_embed]`: Both text and image queries are embedded using model `"gemini-embedding-2"` with `output_dimensionality=768` (`EMBEDDING_DIM`) so query vectors match indexed Firestore embeddings.
- `[repository.py:ProductCatalogRepository.find_similar_products]`: Vector queries require an async `firestore.AsyncClient` and search collection `"products"` on `vector_field="image_embeddings"` using `DistanceMeasure.COSINE` (default `limit=3`).
- `[repository.py:ProductCatalogRepository.format_products_to_string]`: Empty search results always return `"No matching products found in the catalog."`; non-empty items render `title`, `parent_sku`, `retail_price` (`R$`), `shortdesc`, and `img_url` delimited by `\n---\n`.
- `[Dockerfile:COPY]`, `[Dockerfile:USER]`: Production container installs locked dependencies via `uv sync --frozen --no-install-project` and executes as `nonroot` on `gcr.io/distroless/python3-debian13:nonroot` with application files owned by `0:65532` (read-only to the runtime user).
- `[cloudbuild.yaml:deploy-catalog-mcp]`: Cloud Run service `catalog-mcp-server` enforces IAM authentication (`--no-allow-unauthenticated`), disables CPU throttling (`--no-cpu-throttling` so background `BatchSpanProcessor` export threads are not throttled), and runs as dedicated service account `catalog-mcp-sa@$PROJECT_ID.iam.gserviceaccount.com`.

## Side Effects

- `[main.py:setup_logging]`, `[main.py:db]`, `[main.py:genai_client]`, `[main.py:setup_telemetry]`, `[main.py:FastAPIInstrumentor.instrument_app]`: Module import of `main.py` reconfigures global root logging, creates a module-global `firestore.AsyncClient(database=database_id)` and Vertex AI `genai.Client(vertexai=True, ...)`, registers the global OpenTelemetry `TracerProvider`, and instruments `app`.
- `[telemetry.py:setup_logging]`: Clears existing root `logging` handlers, sets root log level to `logging.INFO`, and attaches a `StreamHandler` emitting JSON log lines to `stderr`.
- `[telemetry.py:setup_telemetry]`, `[telemetry.py:flush_telemetry]`: Exports trace spans asynchronously over the network to Google Cloud Trace via `BatchSpanProcessor(CloudTraceSpanExporter)` and force-flushes/shuts down the `TracerProvider` (`FLUSH_TIMEOUT_MILLIS = 3000`) on FastAPI shutdown.
- `[catalog_service.py:_embed]`: Performs outbound async Vertex AI `aio.models.embed_content` RPC calls for each text or image search tool invocation.
- `[repository.py:ProductCatalogRepository.find_similar_products]`: Performs outbound async Google Cloud Firestore `find_nearest` vector stream reads against the `"products"` collection.
- `[cloudbuild.yaml:build-catalog-mcp]`, `[cloudbuild.yaml:push-catalog-mcp]`, `[cloudbuild.yaml:deploy-catalog-mcp]`: CI/CD execution builds and pushes container images to Artifact Registry (`southamerica-east1-docker.pkg.dev/$PROJECT_ID/sre-genai/catalog-mcp-server`) and deploys revisions to Cloud Run in `southamerica-east1`.

## Verification

- Run: `uv run --directory catalog-mcp python -m unittest discover -s tests`
