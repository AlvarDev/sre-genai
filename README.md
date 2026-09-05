# SRE GenAI - Google Store Multimodal Virtual Assistant

Production-grade demonstration platform showcasing **Multimodal Retrieval-Augmented Generation (RAG)**, **Model Context Protocol (MCP)**, **Dual-Layer Safety Guardrails**, and **Site Reliability Engineering (SRE)** monitoring on Google Cloud Platform (GCP) and Firebase.

---

## 🏛️ System Architecture

```
                    +-----------------------------------+
                    |         Nuxt 3 Frontend           |
                    |   (Anonymous Firebase Auth)       |
                    +-----------------+-----------------+
                                      | HTTP / JSON & Form
                                      v
                    +-----------------+-----------------+
                    |     FastAPI Agent Backend         |
                    |  (Google ADK + Guardrails + OTel) |
                    +--------+----------------+---------+
                             |                |
              Pre & Post LLM |                | SSE (MCP Protocol)
                 Guardrails  |                | + OIDC Auth Cache
                             v                v
                +------------+----+  +--------+----------+
                |  Gemini 3.1     |  | FastMCP Catalog   |
                |  Flash / Lite   |  | Service (Port     |
                +-----------------+  | 8001)             |
                                     +--------+----------+
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
* **Model Context Protocol (MCP)**: Microservice separation of product catalog tools using `FastMCP` over Server-Sent Events (SSE).
* **Dual-Layer Guardrail Protection**:
  * **Pre-LLM Guardrail**: Inputs are audited for prompt injection and jailbreak attempts using `gemini-3.1-flash-lite`.
  * **Post-RAG Guardrail**: Database responses are audited to silently strip off-topic item drift (e.g., injected grocery items like potatoes).
* **SRE Telemetry & Observability**: OpenTelemetry metrics exported directly to GCP Cloud Monitoring tracking daily token usage, inference latency, and guardrail violation rates.
* **Automated CI/CD Quality Gating**: `CloudBuild` pipeline integrating Vertex AI Evaluation (`EvalTask`) to test instruction following and coherence prior to Cloud Run deployment.

---

## 📁 Repository Structure

* `backend/`: FastAPI service using `google-adk`, OpenTelemetry, and Firebase Admin SDK.
* `catalog-mcp/`: FastMCP server running over SSE transport for Firestore vector search.
* `frontend/`: Nuxt 3 / Vue 3 web interface with Google brand palette and Firebase anonymous authentication.
* `docs/`: Technical guides for architecture, Cloud Run deployment, and microservice testing.
* `scripts/`: DB seeding (`seed_db.py`), SRE drift injection (`inject_drift.py`), CI/CD quality gate (`eval_test.py`), and admin claims (`manage_admin_claims.py`).
* `k8s/`: Kubernetes deployment and service manifests for Minikube deployment.
* `dashboards/`: Cloud Monitoring dashboard definition for token consumption and guardrail metrics.
* `cloudbuild.yaml`: GCP Cloud Build pipeline definition.

---

## 📚 Documentation Index

* 🚀 **[Cloud Run Deployment Guide](docs/deployment-cloudrun.md)**: Backend service build and deployment parameters (`--no-cpu-throttling`, environment models).
* ☸️ **[Minikube Local Development Guide](docs/deployment-minikube.md)**: Sizing flags (`--cpus 6 --memory 7200m`), GCP auth addon, ext4 model storage, and Skaffold workflow.
* 🧪 **[Backend Testing Guide](docs/testing-backend.md)**: Local testing workflows with Firebase Auth Emulator and `curl`.
* ⚡ **[Catalog MCP Testing Guide](docs/testing-mcp.md)**: Manual JSON-RPC 2.0 SSE protocol testing for catalog tools.
* 📦 **Microservice Specs**:
  * [Backend Service Readme](backend/README.md)
  * [Catalog MCP Server Readme](catalog-mcp/README.md)
  * [Frontend Web App Readme](frontend/README.md)

---

## 🛠️ Local Development & Deployment

### Prerequisite: Firebase Auth Emulator
```bash
npx -y firebase-tools@latest emulators:start --only auth
```

### 🔑 Presenter Admin Mode & Model Switcher
Public attendees default to Vertex AI (Gemini). To unlock the settings drawer and switch to local sidecar inference (Gemma):

1. **Manage Admin Claim**:
   ```bash
   # Grant admin access
   uv run scripts/manage_admin_claims.py --project-id sre-demos --email <your-email> --grant

   # Inspect claims: --list | Revoke claims: --revoke
   ```

2. **Activate in Browser**:
   Tap the Google logo **7 times** to trigger the developer Easter egg, sign in with your Google account, and use the three-dots menu (`⋮`) to switch models.

### Deploying via Kubernetes (Minikube & Skaffold)

1. **Start Minikube with required sizing & GCP Auth**:
   ```bash
   minikube start --driver=docker --cpus=6 --memory=7200m --addons=gcp-auth
   ```
2. **Provision local model weights into Minikube storage**:
   ```bash
   minikube ssh "sudo mkdir -p /var/models && sudo chown -R docker:docker /var/models"
   minikube cp models/gemma-4-E2B-it-Q4_K_M.gguf /var/models/gemma-4-E2B-it-Q4_K_M.gguf
   ```
3. **Start Skaffold dev loop**:
   ```bash
   skaffold dev
   ```
   *(See [Minikube Local Development Guide](docs/deployment-minikube.md) for complete setup instructions).*

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

