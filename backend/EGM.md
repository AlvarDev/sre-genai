# SRE GenAI Agent Backend (`backend`)

## Overview

FastAPI backend service (`sre-genai-backend`, Python `>=3.11`) hosting the Google Store conversational and visual-search assistant (`main:app`). Provides Firebase ID token authentication and zero-trust `sre_genai_admin` role enforcement (`auth.py`), fail-fast runtime configuration and Firestore client bootstrap (`config.py`), strict CORS enforcement (`cors.py`), Firestore conversation persistence (`database.py`), Pydantic request/response schemas (`models.py`), Google Cloud Logging/Monitoring/Trace OpenTelemetry instrumentation (`telemetry.py`), and magic-byte/stream-capped upload validation (`validation.py`). Integrates HTTP route handlers ([`./routers/EGM.md`](./routers/EGM.md)), ADK agent orchestration and guardrails ([`./agent/EGM.md`](./agent/EGM.md)), and outbound Streamable HTTP Model Context Protocol calls to the catalog service ([`../catalog-mcp/EGM.md`](../catalog-mcp/EGM.md)), packaged as a multi-stage distroless container (`Dockerfile`) deployed to Cloud Run as `backend-gemini` and sidecar-backed `backend-gemma` (`cloudbuild.yaml`, `cloudrun-gemma.yaml`).

## Interface

- `[pyproject.toml:project]` — Python package manifest `sre-genai-backend` (`version = "0.1.0"`, `requires-python = ">=3.11"`).
- `[main.py:app]` — Root `FastAPI(title="SRE GenAI Agent Backend", lifespan=lifespan)` application mounting CORS middleware, `POST /chat`, `POST /visual-search`, `GET /health`, and OpenTelemetry FastAPI instrumentation.
- `[auth.py:security]` — `HTTPBearer()` FastAPI security scheme extracting `Authorization: Bearer <token>` credentials.
- `[auth.py:INVALID_TOKEN_DETAIL]` — Generic HTTP 401 error message (`"Token de autenticação inválido ou expirado."`).
- `[auth.py:get_current_user_uid]` — `def get_current_user_uid(credentials: HTTPAuthorizationCredentials = Depends(security)) -> str` validating Firebase JWTs via `firebase_admin.auth.verify_id_token` and returning `decoded_token["uid"]`.
- `[auth.py:require_admin_user]` — `def require_admin_user(credentials: HTTPAuthorizationCredentials = Depends(security)) -> str` requiring both a valid Firebase JWT and truthy `sre_genai_admin` custom claim.
- `[config.py:project_id]`, `[config.py:service_name]`, `[config.py:database_id]`, `[config.py:db]` — Module-level configuration attributes (`PROJECT_ID`, resolved `K_SERVICE` or `SERVICE_NAME`, `FIRESTORE_DATABASE`, and `google.cloud.firestore.Client`).
- `[config.py:lifespan]` — `@asynccontextmanager async def lifespan(app: FastAPI)` calling `flush_telemetry()` on shutdown.
- `[config.py:setup_cors]` — `def setup_cors(app: FastAPI)` parsing `ALLOWED_ORIGINS` and attaching `CORSMiddleware`.
- `[config.py:setup_telemetry]` — Re-export of `[telemetry.py:setup_telemetry]` imported by `main.py` (`from config import lifespan, setup_cors, setup_telemetry`).
- `[cors.py:parse_allowed_origins]` — `def parse_allowed_origins(raw: str | None) -> list[str]` parsing comma-separated explicit origins.
- `[cors.py:add_cors]` — `def add_cors(app: FastAPI, origins: list[str]) -> None` configuring `CORSMiddleware` on `app`.
- `[database.py:get_session_history]` — `def get_session_history(session_id: str, user_uid: str) -> list` reading conversation messages from Firestore `users/{user_uid}/conversations/{session_id}`.
- `[database.py:save_session_history]` — `def save_session_history(session_id: str, messages: list, user_uid: str)` writing truncated conversation messages to Firestore `users/{user_uid}/conversations/{session_id}`.
- `[models.py:ChatRequest]` — Pydantic `BaseModel` with `message: str = Field(min_length=1, max_length=MAX_MESSAGE_CHARS)` and `session_id: str`.
- `[models.py:ChatResponse]` — Pydantic `BaseModel` with `text: str`, `session_id: str`, and `products: list = []`.
- `[telemetry.py:provider]`, `[telemetry.py:tracer_provider]`, `[telemetry.py:FLUSH_TIMEOUT_MILLIS]` — Global `MeterProvider | None`, `TracerProvider | None`, and `3000` ms shutdown flush timeout constant.
- `[telemetry.py:CloudLoggingFormatter]` — `logging.Formatter` serializing structured JSON logs with `logging.googleapis.com/trace`, `logging.googleapis.com/spanId`, and `logging.googleapis.com/trace_sampled`.
- `[telemetry.py:setup_logging]` — `def setup_logging(project_id: str | None)` configuring the root logger at `INFO` with `CloudLoggingFormatter`.
- `[telemetry.py:build_instance_id]` — `def build_instance_id() -> str` generating `<K_REVISION|local>-<8-hex-uuid>` per-process `service.instance.id` values.
- `[telemetry.py:init_telemetry]` — `def init_telemetry(service_name: str, project_id: str | None)` registering `CloudMonitoringMetricsExporter` and `CloudTraceSpanExporter`.
- `[telemetry.py:flush_telemetry]` — `def flush_telemetry()` force-flushing and shutting down metric and trace providers within `FLUSH_TIMEOUT_MILLIS`.
- `[telemetry.py:setup_telemetry]` — `def setup_telemetry(app: FastAPI)` instrumenting `app` via `FastAPIInstrumentor.instrument_app(app, exclude_spans=["receive", "send"])`.
- `[validation.py:ALLOWED_IMAGE_TYPES]`, `[validation.py:MAX_IMAGE_BYTES]`, `[validation.py:MAX_MESSAGE_CHARS]` — Input validation constants (`frozenset({"image/jpeg", "image/png", "image/webp"})`, `10485760` bytes, `2000` characters).
- `[validation.py:detect_image_type]` — `def detect_image_type(data: bytes) -> str | None` inspecting magic bytes for JPEG, PNG, and WebP.
- `[validation.py:read_capped]` — `async def read_capped(upload, limit: int) -> bytes` reading at most `limit + 1` bytes and raising `ValueError` if exceeded.
- `[system_prompt.txt]` — Checked-in reference prompt text for the Google Store Virtual Assistant (runtime prompt loading occurs via Vertex AI Prompt Management in [`./agent/EGM.md`](./agent/EGM.md)).
- `[Dockerfile:ENTRYPOINT]` — Multi-stage `python:3.13-slim` (`uv sync --frozen --no-install-project`) to `gcr.io/distroless/python3-debian13:nonroot` image running `uvicorn main:app --host 0.0.0.0 --port 8080`.
- `[cloudbuild.yaml:steps]`, `[cloudrun-gemma.yaml:metadata.name]` — Cloud Build pipeline and Knative `Service` spec deploying `backend-gemini` and multi-container `backend-gemma` (`backend-service` + `inference-sidecar` with GCS FUSE `/models`) in `southamerica-east1`.
- **Child Subdirectories**:
  - [`./agent`](./agent/EGM.md) — ADK agent orchestration, Vertex AI Prompt Management loader, pre-LLM and post-RAG guardrails, and Streamable HTTP MCP client ([`../catalog-mcp/EGM.md`](../catalog-mcp/EGM.md)).
  - [`./routers`](./routers/EGM.md) — FastAPI route registration for `POST /chat`, `POST /visual-search`, and `GET /health`.

## Invariants

- `[config.py:service_name]` — Requires `K_SERVICE` or `SERVICE_NAME` to be non-empty at import time or raises `RuntimeError`.
- `[config.py:database_id]` — Requires `FIRESTORE_DATABASE` to be non-empty at import time or raises `RuntimeError`.
- `[cors.py:parse_allowed_origins]`, `[cors.py:add_cors]` — `ALLOWED_ORIGINS` must contain at least one explicit origin and must never include `"*"` (raises `RuntimeError`); CORS locks `allow_credentials=False`, `allow_methods=["GET", "POST"]`, and `allow_headers=["Authorization", "Content-Type"]`.
- `[auth.py:get_current_user_uid]`, `[auth.py:require_admin_user]` — Token verification failures raise `HTTPException(status_code=401, detail=INVALID_TOKEN_DETAIL)` without echoing underlying errors; when `SERVICE_NAME == "backend-gemma"` or `K_SERVICE == "backend-gemma"` (or inside `require_admin_user`), tokens without truthy `sre_genai_admin` raise `HTTPException(status_code=403)`.
- `[models.py:ChatRequest]` — Enforces `1 <= len(message) <= MAX_MESSAGE_CHARS` (`2000`).
- `[validation.py:detect_image_type]`, `[validation.py:read_capped]` — Ignores client `Content-Type` headers in favor of magic-byte inspection (`\xff\xd8\xff`, `\x89PNG\r\n\x1a\n`, `RIFF....WEBP`) and bounds upload memory consumption to `limit + 1` bytes before raising `ValueError`.
- `[database.py:get_session_history]`, `[database.py:save_session_history]` — Scope user conversations strictly under `users/{user_uid}/conversations/{session_id}` and truncate persisted history to the last 10 turns (`messages[-10:]`).
- `[telemetry.py:FLUSH_TIMEOUT_MILLIS]` — Bounds shutdown force-flush calls to `3000` ms per provider within Cloud Run's 10 s SIGTERM grace period.
- `[Dockerfile:USER]` — Runs as `nonroot` with code copied `--chown=0:65532` so application files are read-only at runtime.
- `[cloudbuild.yaml:steps]`, `[cloudrun-gemma.yaml:annotations]` — Deploy dedicated service account `backend-sa@$PROJECT_ID.iam.gserviceaccount.com` in `southamerica-east1`; `backend-gemma` enforces `run.googleapis.com/maxScale: '1'` and mounts `gemma-models-volume` `readOnly: true`.

## Side Effects

- `[config.py:setup_logging]`, `[config.py:init_telemetry]`, `[config.py:firebase_admin.initialize_app]`, `[config.py:db]` — At import time, replace root logger handlers with JSON `CloudLoggingFormatter`, initialize OpenTelemetry `MeterProvider` and `TracerProvider` background exporters (`OTEL_EXPORT_INTERVAL_MS`, default `60000` ms), initialize the default `firebase_admin` app if not already initialized, and instantiate `google.cloud.firestore.Client`.
- `[main.py:app]` — At import time, constructs `FastAPI`, validates `ALLOWED_ORIGINS` and attaches `CORSMiddleware`, imports and registers routes from [`./routers/EGM.md`](./routers/EGM.md) (which in turn imports [`./agent/EGM.md`](./agent/EGM.md), triggering Vertex AI and MCP client initialization), and instruments `app` with `FastAPIInstrumentor`.
- `[config.py:lifespan]`, `[telemetry.py:flush_telemetry]` — Force-flush and shut down global OpenTelemetry metric and trace providers on application shutdown.
- `[auth.py:get_current_user_uid]`, `[auth.py:require_admin_user]` — Verify Firebase ID tokens via `firebase_admin.auth.verify_id_token` (fetching/caching Google public keys) and emit warning logs on verification failure.
- `[database.py:get_session_history]`, `[database.py:save_session_history]` — Perform synchronous Firestore `get()` and `set(..., merge=True)` RPCs (including `firestore.SERVER_TIMESTAMP`) against `users/{user_uid}/conversations/{session_id}`.

## Verification

- Run: `uv run --directory backend python -m unittest discover -s tests`
