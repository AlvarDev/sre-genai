# SRE GenAI (Google Store Multimodal Virtual Assistant) Blueprint

## System Overview
`sre-genai` is a multi-service e-commerce Retrieval-Augmented Generation (RAG) reference architecture built on Google Cloud Run, Firebase Authentication, Cloud Firestore, Vertex AI, and the Model Context Protocol (MCP). Shoppers interact with a Nuxt 3 / Vue 3 web client (`frontend`) that authenticates visitors via Firebase Authentication (anonymous guests by default, or Google OAuth users carrying the `sre_genai_admin` custom claim) and sends conversational text (`POST /chat`) and multimodal image queries (`POST /visual-search`) to a FastAPI / Google Agent Development Kit (`google-adk`) orchestrator (`backend`).

Within `backend`, inputs pass through a fail-closed Pre-LLM safety classifier (`gemini-3.5-flash-lite`) before invoking the core agent (`gemini-3.8-flash` on Vertex AI in `backend-gemini`, or `gemma-4-e2b` via an OpenAI-compatible `llama.cpp` sidecar in `backend-gemma`). Product discovery is delegated over stateless Streamable HTTP (`/mcp/`, authenticated with Google OIDC ID tokens on Cloud Run and correlated via W3C `traceparent` headers) to `catalog-mcp`, which generates 768-dimensional multimodal embeddings (`gemini-embedding-2`) and executes Cosine nearest-neighbor vector searches against the Firestore `products` collection. Retrieved items are audited by a Post-RAG guardrail (`gemini-3.5-flash-lite`) to strip off-topic catalog drift before structured product cards and session history (`users/{user_uid}/conversations/{session_id}`) are returned.

```
+-----------------------+     HTTPS + Firebase Bearer JWT      +-------------------------------+
|       frontend        | -----------------------------------> |            backend            |
|  (Nuxt 3 / Vue 3 UI)  |     POST /chat, POST /visual-search  |  (FastAPI + ADK + Guardrails) |
+-----------------------+                                      +-------+---------------+-------+
                                                                       |               |
                                       Streamable HTTP POST /mcp/      |               | Sync Read/Write
                                       (Google OIDC + W3C traceparent) |               | (users/{uid}/
                                                                       v               |  conversations)
                                                               +-------+-------+       v
                                                               |  catalog-mcp  |  +----+---------------+
                                                               |   (FastMCP)   |  |  Cloud Firestore   |
                                                               +-------+-------+  | (Database:         |
                                                                       |          |  FIRESTORE_DATABASE|
                                                                       +--------> |  products & users) |
                                                                 Async Cosine     +--------------------+
                                                                 Vector Search             ^
                                                                 (768-dim)                 | Seed / Drift
                                                                                   +-------+-------+
                                                                                   |    scripts    |
                                                                                   |   (uv CLI)    |
                                                                                   +---------------+
```

## Subdirectories & System Boundaries
- **backend**: [./backend/EGM.md](./backend/EGM.md) - FastAPI + Google ADK agent backend (`sre-genai-backend`, port `8080`) enforcing Firebase JWT verification, `sre_genai_admin` RBAC on `backend-gemma`, strict CORS, upload magic-byte/size validation, Pre-LLM and Post-RAG safety guardrails ([./backend/agent/EGM.md](./backend/agent/EGM.md)), HTTP routing ([./backend/routers/EGM.md](./backend/routers/EGM.md)), Firestore session persistence, and OpenTelemetry export to Cloud Monitoring, Cloud Trace, and Cloud Logging.
- **catalog-mcp**: [./catalog-mcp/EGM.md](./catalog-mcp/EGM.md) - Stateless FastMCP + FastAPI microservice (`sre-genai-catalog-mcp`, port `8001`, mounted at `/mcp`) exposing `search_catalog` and `search_catalog_by_image` backed by Vertex AI `gemini-embedding-2` (768-dim) and Firestore `find_nearest` Cosine vector queries, with Cloud Trace and structured JSON logging.
- **frontend**: [./frontend/EGM.md](./frontend/EGM.md) - Nuxt 3 / Vue 3 web client (`google-store-assistant-frontend`, port `3000`) providing the root shell, dark/light theme state, Firebase Anonymous and Google OAuth authentication, 7-click admin unlock, Gemini/Gemma backend switcher, and conversational/visual shopping UI ([./frontend/pages/EGM.md](./frontend/pages/EGM.md)).
- **scripts**: [./scripts/EGM.md](./scripts/EGM.md) - Standalone PEP 723 (`uv run`) operational CLI utilities for seeding `products/{parent_sku}` from `./scripts/image_data_with_embeddings.csv`, injecting/removing synthetic off-topic grocery vector drift (`organic-potatoes`, `fresh-bananas`), and managing Firebase Auth `sre_genai_admin` custom claims.
- **Non-Code Infrastructure & Configuration Directories** *(no `EGM.md` contract)*:
  - `llama-server/` ([./llama-server/Dockerfile](./llama-server/Dockerfile), [./llama-server/cloudbuild.yaml](./llama-server/cloudbuild.yaml)): Distroless C++ `llama.cpp` HTTP inference sidecar container used by `backend-gemma`.
  - `k8s/` & [./skaffold.yaml](./skaffold.yaml): Local KinD Kubernetes manifests, Workload Identity Federation ConfigMap hooks, and Skaffold profiles (`default`, `backends-only`).
  - `dashboards/` ([./dashboards/token_consumption.json](./dashboards/token_consumption.json)): Google Cloud Monitoring mosaic dashboard tracking token usage, guardrail violations, agent tool-call loops, and `p95` inference/tool latency.
  - `docs/`: Architecture Decision Records, Cloud Run and KinD deployment guides, testing guides, and the talk-day operational runbook.

## Global Invariants
- **End-to-End Authentication & RBAC Boundary**: Every `POST /chat` and `POST /visual-search` request from `frontend` (`[frontend/pages/index.vue:submitMessage]`) must carry a valid Firebase ID token in `Authorization: Bearer <token>`, verified by `backend` (`[backend/auth.py:get_current_user_uid]`). Routing to `backend-gemma` additionally requires the Firebase custom claim `sre_genai_admin == True` (`[frontend/pages/index.vue:loginWithGoogle]`, `[backend/auth.py:get_current_user_uid]`, `[scripts/manage_admin_claims.py:manage_claims]`).
- **Service-to-Service MCP Transport & Auth Contract**: `backend` (`[backend/agent/search.py:call_mcp_tool]`) and `catalog-mcp` (`[catalog-mcp/main.py:mcp]`) must agree on stateless Streamable HTTP at `/mcp` (`stateless_http=True`, `json_response=True`). When `K_SERVICE` is set on Cloud Run, `backend` attaches a Google OIDC identity token scoped to `{scheme}://{netloc}` of `MCP_SERVER_URL`, while `catalog-mcp-server` is deployed with `--no-allow-unauthenticated` (`[catalog-mcp/cloudbuild.yaml:deploy-catalog-mcp]`).
- **Vector Embedding Dimensionality & Schema**: All catalog writers and readers (`[scripts/seed_db.py:generate_embeddings_and_seed]`, `[scripts/inject_drift.py:inject_database_drift]`, `[catalog-mcp/catalog_service.py:EMBEDDING_DIM]`, `[catalog-mcp/repository.py:ProductCatalogRepository.find_similar_products]`) operate on Firestore collection `products` using field `image_embeddings` with fixed 768-dimensional vectors (`gemini-embedding-2`, `DistanceMeasure.COSINE`).
- **Multi-Tenant Session Isolation & Input Bounds**: User conversation history is strictly partitioned under `users/{user_uid}/conversations/{session_id}` and capped to the trailing 10 messages (`[backend/database.py:save_session_history]`). Both client and server enforce a 2,000-character message limit (`MAX_MESSAGE_CHARS = 2000`) and restrict visual uploads to JPEG/PNG/WebP (`<= 10 MiB` magic-byte verified on `backend`).
- **Fail-Closed Safety & Sanitized Error Boundaries**: Pre-LLM jailbreak checks and Post-RAG catalog drift audits fail closed on model, parse, or network errors (`[backend/agent/guardrail.py:validate_user_input]`, `[backend/agent/guardrail.py:filter_retrieved_products]`). Neither `backend` (`GENERIC_ERROR_DETAIL`, `CATALOG_ERROR_MESSAGE`) nor `catalog-mcp` (`TOOL_ERROR_MESSAGE`) exposes raw server exception text to callers; details are recorded only in trace spans and structured logs.
- **Container & Cloud Run Hardening**: All deployable services (`backend`, `catalog-mcp`, `frontend`, `llama-server`) run as `nonroot` inside Google `distroless` base images, deploy to `southamerica-east1` under dedicated per-service IAM Service Accounts (`backend-sa`, `catalog-mcp-sa`, `frontend-sa`), and forbid wildcard `*` CORS origins (`[backend/cors.py:parse_allowed_origins]`).

## Global Side Effects
- **Cloud Firestore (`FIRESTORE_DATABASE`)**: Read/written by `backend` (`users/{user_uid}/conversations/{session_id}`), queried via async vector search by `catalog-mcp` (`products`), and seeded/mutated by `scripts` (`products/{parent_sku}`).
- **Vertex AI APIs**: Invoked by `backend` for system prompt retrieval (`prompts.get`), guardrail classification (`gemini-3.5-flash-lite`), and primary agent reasoning (`gemini-3.8-flash`), and by `catalog-mcp` and `scripts/inject_drift.py` for 768-dimensional multimodal embeddings (`gemini-embedding-2`).
- **Firebase Authentication**: Used client-side by `frontend` (Anonymous and Google OAuth sign-in, token refresh), verified server-side by `backend` (`firebase_admin.auth.verify_id_token`), and mutated administratively by `scripts/manage_admin_claims.py` (`set_custom_user_claims`).
- **Google Cloud Observability**: `backend` exports custom and ADK OpenTelemetry metrics (`google_store.guardrail.violations`, `gen_ai.*`) to Cloud Monitoring (`PeriodicExportingMetricReader`), both `backend` and `catalog-mcp` export distributed traces correlated across HTTP via W3C `traceparent` to Cloud Trace (`BatchSpanProcessor`), and both emit trace-correlated JSON logs to Cloud Logging (`stdout`/`stderr`).
- **Google Cloud Build, Artifact Registry, Cloud Run & Secret Manager**: Service `cloudbuild.yaml` pipelines build/push images to `southamerica-east1-docker.pkg.dev/$PROJECT_ID/sre-genai/*`, deploy Cloud Run services in `southamerica-east1`, mount GCS bucket `${PROJECT_ID}-files` via GCS FUSE on `backend-gemma`, and inject `firebase-web-api-key` from Secret Manager on `frontend-service` and local Skaffold hooks.

## System Verification
- Run backend unit tests: `uv run --directory backend python -m unittest discover -s tests`
- Run catalog-mcp unit tests: `uv run --directory catalog-mcp python -m unittest discover -s tests`
- Run frontend production build check: `yarn --cwd frontend build`
