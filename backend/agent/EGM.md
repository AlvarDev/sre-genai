# Backend Agent Package (`backend/agent`)

## Overview

Conversational e-commerce agent package implementing Google ADK orchestration (`google-adk`), Vertex AI Prompt Management caching (`vertexai.preview.prompts`), dual-layer fail-closed security guardrails (`google-genai`), and stateless Streamable HTTP Model Context Protocol (MCP) catalog search (`mcp`) against [`../../catalog-mcp/EGM.md`](../../catalog-mcp/EGM.md). Serves text and multimodal chat invocations from the HTTP router layer ([`../routers/EGM.md`](../routers/EGM.md)) within the backend service ([`../EGM.md`](../EGM.md)).

## Interface

- `[catalog_messages.py:CATALOG_ERROR_MESSAGE]` — Shared Portuguese fallback constant (`"Erro ao consultar o catálogo."`) returned on MCP tool failures and recognized by post-RAG drift filtering.
- `[guardrail.py:GuardrailException]` — `Exception` subclass raised when pre-LLM input validation blocks unsafe prompts or encounters a system failure.
- `[guardrail.py:model_name]` — Module-level guardrail model identifier resolved from `GUARDRAIL_MODEL` (default `"gemini-3.5-flash-lite"`).
- `[guardrail.py:INPUT_CHECK_MAX_OUTPUT_TOKENS]` — Output token ceiling (`512`) for pre-LLM input classification.
- `[guardrail.py:DRIFT_AUDIT_MAX_OUTPUT_TOKENS]` — Output token ceiling (`1024`) for post-RAG catalog drift auditing.
- `[guardrail.py:validate_user_input]` — `async def validate_user_input(user_query: str) -> str` classifying user text for prompt injections/jailbreaks via Vertex AI Gemini (`GUARDRAIL_MODEL`, default `"gemini-3.5-flash-lite"`), returning `user_query` when safe or raising `GuardrailException`.
- `[guardrail.py:filter_retrieved_products]` — `async def filter_retrieved_products(raw_search_results: str) -> str` auditing `"\n---\n"`-delimited catalog items via Vertex AI Gemini and stripping `"OFF-TOPIC"` SKUs before returning results to the agent.
- `[guardrail_metrics.py:VIOLATION_TYPES]` — Bounded `tuple[str, ...]` of violation labels (`"input_jailbreak"`, `"database_drift"`, `"guardrail_system_failure"`, `"guardrail_database_drift_failure"`).
- `[guardrail_metrics.py:GUARDRAIL_AGENT_NAME]` — Constant `"guardrail"` recorded as `gen_ai.agent.name`.
- `[guardrail_metrics.py:PROVIDER_NAME]` — Constant `"vertex_ai"` recorded as `gen_ai.provider.name`.
- `[guardrail_metrics.py:token_usage_points]` — `def token_usage_points(usage_metadata, request_model: str, response_model: str | None) -> list[tuple[int, dict]]` computing ADK-compatible input/output token metric points for `gen_ai.client.token.usage`.
- `[log_utils.py:summarize_tool_args]` — `def summarize_tool_args(arguments: dict, max_len: int = 256) -> dict` redacting string values longer than `max_len` to `"<str len=N>"` for safe logging.
- `[orchestrator.py:VERTEX_PROMPT_ID]`, `[orchestrator.py:PROMPT_CACHE_TTL]` — Vertex AI Prompt Management resource ID and in-memory cache TTL in seconds (`PROMPT_CACHE_TTL_SECONDS`, default `600`).
- `[orchestrator.py:current_image_bytes]`, `[orchestrator.py:current_image_mime]` — Request-scoped `contextvars.ContextVar` instances propagating active upload bytes and MIME type to `search_catalog_by_image`.
- `[orchestrator.py:model_name]`, `[orchestrator.py:core_model]` — Module-level core LLM name resolved from `CORE_MODEL` (default `"gemini-3.8-flash"`) and instantiated ADK model wrapper (`Gemini` on Vertex AI or `LiteLlm` when `"gemma"` is in `model_name.lower()`).
- `[orchestrator.py:store_assistant_agent]` — Singleton `google.adk.agents.Agent` (`name="store_assistant"`, `max_output_tokens=4096`) backed by `core_model`.
- `[orchestrator.py:get_system_instruction]` — `def get_system_instruction() -> str` retrieving and TTL-caching the system prompt from `vertexai.preview.prompts.get`.
- `[orchestrator.py:search_catalog_by_text]` — `async def search_catalog_by_text(query_text: str) -> str` ADK tool chaining `call_catalog_text_search` with `filter_retrieved_products`.
- `[orchestrator.py:search_catalog_by_image]` — `async def search_catalog_by_image() -> str` ADK tool base64-encoding `current_image_bytes` and chaining `call_catalog_image_search` with `filter_retrieved_products`.
- `[orchestrator.py:parse_structured_products]` — `def parse_structured_products(clean_results: str) -> list[dict]` parsing `"---"`-delimited catalog blocks into UI dictionaries (`title`, `parent_sku`, `retail_price`, `shortdesc`, `img_url`).
- `[orchestrator.py:execute_text_chat]` — `async def execute_text_chat(user_query: str, chat_history: list, user_uid: str = "") -> dict` running input guardrails, hydrating ephemeral `InMemorySessionService` history, running the ADK `Runner`, and returning `{"text": str, "products": list[dict]}`.
- `[orchestrator.py:execute_visual_chat]` — `async def execute_visual_chat(image_bytes: bytes, user_query: str = "", chat_history: list = None, user_uid: str = "", mime_type: str = "image/jpeg") -> dict` executing multimodal ADK turns with optional text guardrail validation and returning `{"text": str, "products": list[dict]}`.
- `[search.py:MCP_HTTP_TIMEOUT]` — `httpx.Timeout(30.0, read=300.0)` transport timeout configuration for MCP calls.
- `[search.py:get_mcp_headers]` — `def get_mcp_headers() -> dict` constructing MCP HTTP headers with Cloud Run Google OIDC `Authorization: Bearer <token>` (when `K_SERVICE` is set) and W3C `traceparent` context.
- `[search.py:build_mcp_http_client]` — `def build_mcp_http_client(headers: dict) -> httpx.AsyncClient` creating an `httpx.AsyncClient` with `MCP_HTTP_TIMEOUT` and `follow_redirects=True`.
- `[search.py:call_mcp_tool]` — `async def call_mcp_tool(tool_name: str, arguments: dict) -> str` performing a stateless Streamable HTTP MCP handshake and `session.call_tool` call against `MCP_SERVER_URL`.
- `[search.py:call_catalog_text_search]` — `async def call_catalog_text_search(query_text: str) -> str` invoking remote MCP tool `"search_catalog"` and returning `CATALOG_ERROR_MESSAGE` on failure.
- `[search.py:call_catalog_image_search]` — `async def call_catalog_image_search(image_base64: str, mime_type: str = "image/jpeg") -> str` invoking remote MCP tool `"search_catalog_by_image"` and returning `CATALOG_ERROR_MESSAGE` on failure.

## Invariants

- `[guardrail.py:project_id]`, `[guardrail.py:gemini_location]`, `[orchestrator.py:project_id]`, `[orchestrator.py:gemini_location]`, `[orchestrator.py:vertex_prompt_location]`, `[orchestrator.py:VERTEX_PROMPT_ID]`, `[search.py:mcp_server_url]` — Mandatory environment variables (`PROJECT_ID`, `GEMINI_LOCATION`, `VERTEX_PROMPT_LOCATION`, `VERTEX_PROMPT_ID`, `MCP_SERVER_URL`) are validated at module import time and raise `RuntimeError` if missing or empty.
- `[orchestrator.py:inference_endpoint]` — When `"gemma"` appears in `CORE_MODEL.lower()`, `INFERENCE_ENDPOINT` is mandatory at import time and raises `RuntimeError` if unset.
- `[orchestrator.py:get_system_instruction]`, `[orchestrator.py:system_instruction]` — Fetches the system prompt eagerly at import time and refreshes after `PROMPT_CACHE_TTL` seconds; empty prompt content or Vertex AI failures fail fast with `RuntimeError` without local fallback.
- `[guardrail.py:validate_user_input]` — Fails closed: defaults missing `"is_safe"` fields to `False`, raises `GuardrailException` on unsafe classifications (`"input_jailbreak"`) and on any model/JSON/network error (`"guardrail_system_failure"`), and runs prior to LLM invocation in `execute_text_chat` (always) and `execute_visual_chat` (whenever `user_query.strip()` is non-empty).
- `[guardrail.py:filter_retrieved_products]` — Fails closed: unless `raw_search_results` is empty, contains `"No matching products"` or `"No visually matching"`, or equals `CATALOG_ERROR_MESSAGE`, audits all retrieved items and returns a static Portuguese error message (`"guardrail_database_drift_failure"`) on any audit exception rather than forwarding unverified database items.
- `[guardrail.py:_record_violation]`, `[guardrail_metrics.py:VIOLATION_TYPES]` — `google_store.guardrail.violations` counter emits only bounded `violation.type` labels pre-seeded with `0` at import time; per-item SKU and reason strings are recorded exclusively on span events.
- `[guardrail_metrics.py:token_usage_points]` — Returns `[]` when `usage_metadata` is `None` and records `"input"` or `"output"` data points only when their summed token counts are strictly greater than `0`.
- `[log_utils.py:summarize_tool_args]`, `[search.py:call_mcp_tool]` — Redacts string tool arguments longer than `256` characters (such as base64 image payloads) before writing to logs.
- `[orchestrator.py:parse_structured_products]` — Deduplicates parsed product dictionaries by `parent_sku` while preserving first-seen order.
- `[orchestrator.py:execute_visual_chat]` — Resets `current_image_bytes` and `current_image_mime` `ContextVar` tokens inside a `finally` block on every call.
- `[search.py:get_mcp_headers]` — When `K_SERVICE` is set, Google OIDC ID token acquisition targeting `{scheme}://{netloc}` of `MCP_SERVER_URL` is mandatory and raises `RuntimeError` on failure; when `K_SERVICE` is unset, `Authorization` is omitted.
- `[search.py:call_catalog_text_search]`, `[search.py:call_catalog_image_search]` — Catch all exceptions from `call_mcp_tool` and return `CATALOG_ERROR_MESSAGE` so raw transport errors are never exposed to the LLM or end user.

## Side Effects

- `[guardrail.py:tracer]`, `[guardrail.py:violations_counter]`, `[guardrail.py:token_usage_histogram]`, `[guardrail.py:client]` — At import time, register OpenTelemetry tracer/meter instruments (`google_store.guardrail.violations`, `gen_ai.client.token.usage`), pre-seed `0` counts for `VIOLATION_TYPES`, and initialize a Vertex AI `google.genai.Client`.
- `[orchestrator.py:vertexai.init]`, `[orchestrator.py:system_instruction]`, `[orchestrator.py:core_model]`, `[orchestrator.py:store_assistant_agent]` — At import time, initialize the Vertex AI SDK, perform a synchronous RPC to `vertexai.preview.prompts.get`, populate module-level prompt cache globals (`_cached_instruction`, `_last_prompt_fetch_time`), and instantiate the LLM model wrapper and `Agent` singleton.
- `[search.py:tracer]`, `[search.py:mcp_server_url]` — At import time, read `MCP_SERVER_URL` and register OpenTelemetry tracer `"backend.mcp-client"`.
- `[guardrail.py:validate_user_input]`, `[guardrail.py:filter_retrieved_products]` — Execute async Vertex AI `client.aio.models.generate_content` RPCs, emit OpenTelemetry spans/events, record counter/histogram metrics, and log via `"guardrail"`.
- `[orchestrator.py:execute_text_chat]`, `[orchestrator.py:execute_visual_chat]` — Mutate `store_assistant_agent.instruction` (triggering synchronous `prompts.get` RPCs on TTL expiry), allocate ephemeral `InMemorySessionService` sessions, mutate/reset `ContextVar` state (visual chat), and stream ADK `Runner.run_async` events (invoking Vertex AI Gemini or LiteLLM endpoints and catalog tools).
- `[search.py:get_mcp_headers]`, `[search.py:call_mcp_tool]` — Acquire Google OIDC ID tokens (`id_token.fetch_id_token`) on a worker thread via `asyncio.to_thread` when `K_SERVICE` is set, inject W3C `traceparent` headers, open outbound Streamable HTTP MCP sessions (`httpx.AsyncClient`, `streamable_http_client`, `ClientSession`) to `MCP_SERVER_URL`, emit OpenTelemetry spans, and log via `"mcp-client"`.

## Verification

- Run: `uv run --directory backend python -m unittest discover -s tests`
