# SRE GenAI - Agent Backend Service

FastAPI backend service built on top of the **Google Agent Development Kit (`google-adk`)**, managing conversational workflows, visual embedding generation, guardrail filtering, and OpenTelemetry instrumentation.

---

## 🛠️ Tech Stack & Dependencies

* **Framework**: FastAPI (running on Uvicorn on port 8080)
* **Agent Engine**: `google-adk` (`Agent`, `Runner`, `InMemorySessionService`)
* **Package Manager**: `uv`
* **Models**: `gemini-3.8-flash` (Core agent orchestrator), `gemini-3.1-flash-lite` (Guardrail classifier) & `gemini-embedding-2` (768-dim embeddings)
* **Authentication**: Firebase Admin SDK & GCP OIDC Token Cache for service-to-service IAM calls
* **Telemetry**: OpenTelemetry SDK with `opentelemetry-exporter-gcp-monitoring`

---

## 🔌 API Endpoints

* `POST /chat`: Text-based chat RAG interaction.
* `POST /visual-search`: Image upload search (multipart/form-data).
* `GET /health`: Health check endpoint.

---

## 🏗️ Internal Components

* `main.py`: FastAPI entrypoint, Firebase auth validation (`get_current_user_uid`), and OpenTelemetry setup.
* `agent/orchestrator.py`: ADK runner execution (`run_text_chat`, `run_visual_search`).
* `agent/guardrail.py`: Pre-LLM jailbreak check & Post-RAG database drift filter (`GuardrailException`).
* `agent/search.py`: SSE client connector for Catalog MCP service with thread-safe OIDC token cache (`OIDCTokenCache`).

