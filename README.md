# SRE GenAI - Google Store Multimodal Virtual Assistant

Reference demonstration platform showcasing **Multimodal Retrieval-Augmented Generation (RAG)**, **Model Context Protocol (MCP)**, **Dual-Layer Safety Guardrails**, and **Site Reliability Engineering (SRE)** monitoring on Google Cloud Platform (GCP) and Firebase.

---

## 🏛️ System Architecture

```
                    +-----------------------------------+
                    |         Nuxt 3 Frontend           |
                    |   (Anonymous & Admin Google Auth) |
                    +-----------------+-----------------+
                                      | Direct HTTP (Bearer Token)
                                      v
                    +------------------------------------+
                    |        FastAPI Agent Backend       |
                    |   (Google ADK + Guardrails + OTel) |
                    +--------+-----------------+---------+
                             |                 |
              Pre & Post LLM |                 | Streamable HTTP (MCP)
                 Guardrails  |                 | + Google OIDC Auth
                             v                 v
     +-----------------------+-----+  +--------+----------+
     |  Gemini 3.8 Flash (Cloud)   |  | FastMCP Catalog   |
     |  or Gemma 4 E2B (Sidecar)   |  | Service (Port     |
     |  + Gemini 3.5 Flash-Lite    |  | 8001)             |
     +-----------------------------+  +--------+----------+
                                               | Vector Search
                                               v
                                      +-------------------+
                                      | Cloud Firestore   |
                                      | (Database:        |
                                      | 'sre-genai')      |
                                      +-------------------+
```

---

## 🚀 Key Features

* **Multimodal Visual & Text Search**: Natural language search and visual query capabilities using `gemini-embedding-2` generating 768-dimensional multimodal vector embeddings.
* **Model Context Protocol (MCP)**: Microservice separation of product catalog tools using `FastMCP` over stateless Streamable HTTP.
* **Dual-Inference Engine & RBAC**: Supports managed **Gemini Enterprise Agent Platform (Vertex AI)** inference (`gemini-3.8-flash`) and self-hosted sidecar inference (`gemma-4-e2b` via `llama-server`) with zero-trust role-based access control (`sre_genai_admin` custom claim enforcement).
* **Dual-Layer Guardrail Protection**:
  * **Pre-LLM Guardrail**: Inputs are audited for prompt injection and jailbreak attempts using `gemini-3.5-flash-lite`.
  * **Post-RAG Guardrail**: Database responses are audited to silently strip off-topic item drift (e.g., injected grocery items like potatoes).
* **SRE Telemetry & Observability**: OpenTelemetry metrics exported directly to GCP Cloud Monitoring tracking daily token usage, inference latency, and guardrail violation rates.

---

## 📁 Repository Structure

* `backend/`: FastAPI service using `google-adk`, OpenTelemetry, and Firebase Admin SDK.
* `catalog-mcp/`: FastMCP server running over stateless Streamable HTTP transport for Firestore vector search.
* `frontend/`: Nuxt 3 / Vue 3 web interface with Google brand palette and Firebase anonymous authentication.
* `llama-server/`: Distroless C++ inference sidecar (`llama.cpp`) serving quantized Gemma 4 E2B weights in-memory.
* `docs/`: Technical guides for architecture, Cloud Run deployment, and microservice testing.
* `scripts/`: DB seeding (`seed_db.py`), SRE drift injection (`inject_drift.py`), and admin claims (`manage_admin_claims.py`).
* `k8s/`: Kubernetes deployment and service manifests for local KinD deployment.
* `dashboards/`: Cloud Monitoring dashboard definition for token consumption and guardrail metrics.
* `*/cloudbuild.yaml`: Per-service GCP Cloud Build pipeline definitions (`backend/`, `catalog-mcp/`, `frontend/`, `llama-server/`).

---

## 📚 Documentation Index

* 🚀 **[Cloud Run Deployment Guide](docs/deployment-cloudrun.md)**: Backend service build and deployment parameters (`--no-cpu-throttling`, environment models).
* 🎤 **[Talk-Day Runbook](docs/talk-day-runbook.md)**: Step-by-step checklist to warm up instances, open/close `allUsers` IAM access for live demos, and roll back revisions.
* ☸️ **[KinD Local Development Guide](docs/deployment-kind.md)**: Rootless Podman cluster setup, Workload Identity Federation, node model storage, and Skaffold workflow.
* 📐 **[ADR: Gemma 4 Sidecar Serving](docs/adr-gemma-sidecar-serving.md)**: Architectural decisions for multi-container Cloud Run GCS FUSE and local in-memory GGUF serving.
* 🧪 **[Backend Testing Guide](docs/testing-backend.md)**: Local testing workflows with `curl` and Firebase Auth.
* ⚡ **[Catalog MCP Testing Guide](docs/testing-mcp.md)**: Manual JSON-RPC 2.0 Streamable HTTP protocol testing for catalog tools.
* 📦 **Microservice Specs**:
  * [Backend Service Readme](backend/README.md)
  * [Catalog MCP Server Readme](catalog-mcp/README.md)
  * [Frontend Web App Readme](frontend/README.md)

---

## 🛠️ Local Development & Deployment

### 🔑 Presenter Admin Mode & Model Switcher
Public attendees default to Gemini Enterprise Agent Platform (Vertex AI — Gemini). To unlock the settings drawer and switch to local sidecar inference (Gemma):

1. **Manage Admin Claim**:
   ```bash
   # Grant admin access
   uv run scripts/manage_admin_claims.py --project-id sre-demos --email <your-email> --grant

   # Inspect claims: --list | Revoke claims: --revoke
   ```

2. **Activate in Browser**:
   Tap the Google logo **7 times** to trigger the developer Easter egg, sign in with your Google account, and use the three-dots menu (`⋮`) to switch models.

### Deploying via Local Kubernetes (KinD & Skaffold)

1. **Create the KinD cluster (with Rootless Podman)**:
   ```bash
   KIND_EXPERIMENTAL_PROVIDER=podman kind create cluster --name gstore-cluster
   ```
2. **Provision local model weights into the KinD node**:
   ```bash
   podman exec gstore-cluster-control-plane mkdir -p /var/models
   podman cp models/gemma-4-E2B-it-Q4_K_M.gguf gstore-cluster-control-plane:/var/models/gemma-4-E2B-it-Q4_K_M.gguf
   podman exec gstore-cluster-control-plane chown -R 65532:65532 /var/models
   podman exec gstore-cluster-control-plane chmod 0640 /var/models/gemma-4-E2B-it-Q4_K_M.gguf
   ```
3. **Start Skaffold dev loop**:
   ```bash
   skaffold dev
   ```
   *(See [KinD Local Development Guide](docs/deployment-kind.md) for Workload Identity Federation setup and full instructions).*

### Production Deployment to Cloud Run

1. **Prerequisite: GCS Bucket & IAM Setup for Gemma Model**:
   ```bash
   export PROJECT_ID=$(gcloud config get-value project 2>/dev/null)
   gcloud storage buckets add-iam-policy-binding gs://${PROJECT_ID}-files \
     --member="serviceAccount:backend-sa@${PROJECT_ID}.iam.gserviceaccount.com" \
     --role="roles/storage.objectViewer"
   ```
2. **Deploy via Cloud Build**:
   Deployments are managed automatically via Cloud Build triggers in `southamerica-east1` upon pushing to `main` (see [Cloud Run Deployment Guide](docs/deployment-cloudrun.md) for full details).

---

## 📄 License & Disclaimer

Licensed under the [Apache License, Version 2.0](LICENSE).

> **Disclaimer:** This repository is a reference demonstration for educational and conference purposes and is not an officially supported Google product.

