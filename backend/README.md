# SRE GenAI - Agent Backend Service

FastAPI backend service built on top of the **Google Agent Development Kit (`google-adk`)**, managing conversational workflows, visual embedding generation, guardrail filtering, and OpenTelemetry instrumentation.

---

## 🛠️ Tech Stack & Dependencies

* **Framework**: FastAPI (running on Uvicorn on port 8080)
* **Agent Engine**: `google-adk` (`Agent`, `Runner`, `InMemorySessionService`)
* **Package Manager**: `uv`
* **Models**: `gemini-3.8-flash` (Core agent via Vertex AI), `gemma-4-e2b` (Local sidecar via LiteLLM / llama-server), `gemini-3.5-flash-lite` (Pre-LLM and Post-RAG guardrails). *Note: `gemini-embedding-2` is managed exclusively by the `catalog-mcp` service.*
* **Prompt Management**: Dynamic system prompt retrieval via Vertex AI Prompt Management (`prompts.get`) with in-memory TTL caching.
* **Authentication**: Firebase Admin SDK (token verification and `sre_genai_admin` RBAC claim enforcement on `backend-gemma`) & Google OIDC Identity Tokens for service-to-service IAM calls to `catalog-mcp`.
* **Telemetry**: OpenTelemetry SDK with `opentelemetry-exporter-gcp-monitoring` (Cloud Monitoring), `opentelemetry-exporter-gcp-trace` (Cloud Trace), and Google Cloud-compliant JSON structured logging with trace/span correlation.

---

## 🔌 API Endpoints

* `POST /chat`: Text-based chat RAG interaction.
* `POST /visual-search`: Image upload search (multipart/form-data).
* `GET /health`: Health check endpoint.

---

## 🏗️ Internal Components

* `main.py`: FastAPI entrypoint, CORS middleware, route registration, and OpenTelemetry setup.
* `auth.py`: Firebase ID token verification (`get_current_user_uid`) and zero-trust role-based access control enforcing the `sre_genai_admin` claim when connecting to `backend-gemma`.
* `agent/orchestrator.py`: ADK runner execution (`execute_text_chat`, `execute_visual_chat`), dynamic prompt loading with TTL cache from Vertex AI Prompt Management (`prompts.get`), and dual-model selector (`Gemini` / `LiteLlm`).
* `agent/guardrail.py`: Pre-LLM jailbreak validation (`validate_user_input`) and Post-RAG database drift filtering (`filter_retrieved_products`) powered by `gemini-3.5-flash-lite`.
* `agent/search.py`: SSE client connector for Catalog MCP service with direct Google OIDC token acquisition and W3C `traceparent` context propagation.
* `database.py`: Firestore session history persistence scoped by user subcollections.
* `routers/chat.py` & `routers/health.py`: HTTP endpoint routing for chat, visual search, and health checks.
* `config.py`: Service lifespan, Firestore database client, and CORS configuration.

---

## 🗄️ Cloud Firestore Data Model & Tenant Isolation

The backend operates against the `sre-genai` Firestore database using the Google Cloud server SDK (`google-cloud-firestore`).

### 1. Conversation History (Hierarchical Tenant Isolation)
To prevent Insecure Direct Object References (IDOR) and enforce multi-tenant isolation, conversation sessions are strictly partitioned under user-scoped subcollections:

* **Path**: `/users/{user_uid}/conversations/{session_id}`
* **Document Structure**:
  ```json
  {
    "user_uid": "string (Firebase Auth UID of session owner)",
    "messages": [
      { "role": "user", "content": "Olá, estou procurando bonés..." },
      { "role": "model", "content": "Encontrei estes modelos disponíveis..." }
    ],
    "updated_at": "SERVER_TIMESTAMP"
  }
  ```
* **Retention Policy**: The backend maintains a sliding window of the last **10 messages** (`messages[-10:]`) to balance conversational context against token consumption and latency.

### 2. Product Catalog (`products` collection)
Queried by the `catalog-mcp` microservice for vector search:
* **Path**: `/products/{sku}`
* **Vector Field**: `image_embeddings` (768-dimensional float vector, indexed with `DistanceMeasure.COSINE`).
