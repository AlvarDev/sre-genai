# Backend HTTP Routers (`backend/routers`)

## Overview

FastAPI route registration package exposing authenticated chat (`POST /chat`) and multimodal visual search (`POST /visual-search`) endpoints alongside an unauthenticated liveness check (`GET /health`). Connects HTTP request validation, Firebase user identity dependencies ([`../EGM.md`](../EGM.md)), Firestore session persistence, OpenTelemetry span enrichment, and agent orchestration ([`../agent/EGM.md`](../agent/EGM.md)).

## Interface

- `[__init__.py]` — Package marker module; exports no symbols.
- `[chat.py:GENERIC_ERROR_DETAIL]` — Constant string (`"Erro interno ao processar sua solicitação."`) returned as the HTTP 500 detail payload on unhandled exceptions.
- `[chat.py:register_chat_routes]` — `def register_chat_routes(app: FastAPI)` registering `POST /chat` and `POST /visual-search` handlers on `app`.
- `[chat.py:chat]` — `POST /chat` (`async def chat(request: ChatRequest, user_uid: str = Depends(get_current_user_uid))`, `response_model=ChatResponse`) returning `ChatResponse(text, session_id, products)`.
- `[chat.py:visual_search]` — `POST /visual-search` (`async def visual_search(image: UploadFile = File(...), message: str = Form(default=""), session_id: str = Form(default=""), user_uid: str = Depends(get_current_user_uid))`) returning a `dict` with keys `"text"`, `"products"`, and `"session_id"`.
- `[health.py:register_health_routes]` — `def register_health_routes(app: FastAPI)` registering `GET /health` on `app`.
- `[health.py:health]` — `GET /health` (`def health()`) returning `{"status": "healthy"}`.

## Invariants

- `[chat.py:chat]`, `[chat.py:visual_search]` — Require an authenticated `user_uid` via `Depends(get_current_user_uid)` and default an empty or missing `session_id` to a new UUIDv4 string (`str(uuid.uuid4())`).
- `[chat.py:visual_search]` — Validates request inputs before any database read (`get_session_history`) or orchestrator invocation (`execute_visual_chat`): raises `HTTPException(status_code=422)` when `len(message) > MAX_MESSAGE_CHARS`, `HTTPException(status_code=413)` when `read_capped(image, MAX_IMAGE_BYTES)` raises `ValueError`, and `HTTPException(status_code=415)` when `detect_image_type(image_bytes)` returns `None`.
- `[chat.py:chat]`, `[chat.py:visual_search]` — Catch `GuardrailException` and return HTTP 200 with `text=str(ge)` and `products=[]` without appending turns or persisting session history.
- `[chat.py:GENERIC_ERROR_DETAIL]`, `[chat.py:chat]`, `[chat.py:visual_search]` — Re-raise `HTTPException` unchanged, catch all other unexpected `Exception` instances, log full tracebacks server-side via `logger.exception(...)`, and raise `HTTPException(status_code=500, detail=GENERIC_ERROR_DETAIL)` so raw exception messages are never leaked to clients.
- `[chat.py:chat]`, `[chat.py:visual_search]` — Offload synchronous Firestore helpers (`get_session_history`, `save_session_history`) off the asyncio event loop via `asyncio.to_thread(...)`.
- `[health.py:health]` — Unauthenticated liveness route unconditionally returning `{"status": "healthy"}`.

## Side Effects

- `[chat.py:logger]` — Initializes module-level logger `logging.getLogger("chat")` at import time.
- `[chat.py:register_chat_routes]`, `[health.py:register_health_routes]` — Mutate the provided `FastAPI` application instance by registering `POST /chat`, `POST /visual-search`, and `GET /health`.
- `[chat.py:chat]`, `[chat.py:visual_search]` — Mutate the active OpenTelemetry span (`trace.get_current_span()`) when `span and span.is_recording()` by setting attributes `"gen_ai.conversation.id"`, `"session_id"`, and `"enduser.id"`.
- `[chat.py:visual_search]` — Consumes the uploaded multipart file stream via `await read_capped(image, MAX_IMAGE_BYTES)`.
- `[chat.py:chat]`, `[chat.py:visual_search]` — Read Firestore session history via `await asyncio.to_thread(get_session_history, ..., user_uid)` and, on successful non-guardrail responses, append `"user"` (prefixed with `"[Buscou por Imagem] "` in `visual_search`) and `"model"` turns and persist via `await asyncio.to_thread(save_session_history, ..., history, user_uid)`.
- `[chat.py:chat]`, `[chat.py:visual_search]` — Invoke `await execute_text_chat(...)` and `await execute_visual_chat(...)` in `agent.orchestrator` ([`../agent/EGM.md`](../agent/EGM.md)).
- `[chat.py:chat]`, `[chat.py:visual_search]` — Emit server error logs with stack traces via `logger.exception("chat failed")` and `logger.exception("visual search failed")` on unhandled exceptions.

## Verification

- Run: `uv run --directory backend python -m unittest discover -s tests`
