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
* `database.py`: Firestore session history persistence scoped by user subcollections.

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
