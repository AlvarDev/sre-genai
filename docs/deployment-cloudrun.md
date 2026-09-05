# Cloud Run Production Deployment Guide

This guide details how to provision prerequisite cloud infrastructure, upload model weights to Google Cloud Storage (GCS), and deploy the backend services to Google Cloud Run in `southamerica-east1`.

---

## 📦 1. Cloud Storage Bucket & Model Weights Provisioning

`backend-gemma` serves the Gemma 4 E2B model using Cloud Run's managed [Cloud Storage volume mount](https://cloud.google.com/run/docs/configuring/services/cloud-storage-volume-mounts) (`gcsfuse.run.googleapis.com`). The storage bucket and model weights must be provisioned before deploying the multi-container service.

### A. Create the Regional GCS Bucket
Create the bucket in the same region as the Cloud Run services (`southamerica-east1`):

```bash
PROJECT_ID=$(gcloud config get-value project 2>/dev/null)

gcloud storage buckets create gs://${PROJECT_ID}-files \
  --location=southamerica-east1 \
  --uniform-bucket-level-access
```

### B. Upload the Gemma Model Weights to GCS

#### Option 1: Direct Transfer via Cloud Build (Recommended — Zero Local Bandwidth)
Downloads the weights directly from Hugging Face onto Google's high-speed data center backbone and streams them straight into the bucket in ~15 seconds:

```bash
gcloud builds submit --no-source --config=- <<EOF
steps:
- name: 'gcr.io/google.com/cloudsdktool/cloud-sdk:slim'
  entrypoint: 'bash'
  args:
  - '-c'
  - |
    curl -L "https://huggingface.co/unsloth/gemma-4-E2B-it-GGUF/resolve/main/gemma-4-E2B-it-Q4_K_M.gguf" -o /tmp/gemma-4-E2B-it-Q4_K_M.gguf
    gcloud storage cp /tmp/gemma-4-E2B-it-Q4_K_M.gguf gs://${PROJECT_ID}-files/gemma-4-E2B-it-Q4_K_M.gguf
EOF
```

#### Option 2: Upload from Local Machine
If you already have `models/gemma-4-E2B-it-Q4_K_M.gguf` downloaded locally:

```bash
gcloud storage cp models/gemma-4-E2B-it-Q4_K_M.gguf gs://${PROJECT_ID}-files/
```

### C. Grant Service Account Read Access
Grant the dedicated `backend-sa` service account read access to the bucket so Cloud Run's GCS FUSE volume mount can access the model:

```bash
gcloud storage buckets add-iam-policy-binding gs://${PROJECT_ID}-files \
  --member="serviceAccount:backend-sa@${PROJECT_ID}.iam.gserviceaccount.com" \
  --role="roles/storage.objectViewer"
```

---

## 🚀 2. Service Deployment

Deployments are managed declaratively via Cloud Build triggers using [`backend/cloudbuild.yaml`](../backend/cloudbuild.yaml).

### Deploying `backend-gemini` (Managed Vertex AI Agent)
```bash
gcloud run deploy backend-gemini \
  --image southamerica-east1-docker.pkg.dev/${PROJECT_ID}/sre-genai/backend-service:latest \
  --region southamerica-east1 \
  --set-env-vars="PROJECT_ID=${PROJECT_ID},LOCATION=us,FIRESTORE_DATABASE=sre-genai,CORE_MODEL=gemini-3.8-flash,GUARDRAIL_MODEL=gemini-3.5-flash-lite,MCP_SERVER_URL=https://catalog-mcp-server-${PROJECT_NUMBER}.southamerica-east1.run.app/mcp/sse" \
  --service-account backend-sa@${PROJECT_ID}.iam.gserviceaccount.com \
  --no-cpu-throttling \
  --allow-unauthenticated
```

### Deploying `backend-gemma` (Multi-Container Sidecar with GCS FUSE)
Deploys the declarative manifest [`backend/cloudrun-gemma.yaml`](../backend/cloudrun-gemma.yaml) with dynamic project substitution:

```bash
sed -i "s/PROJECT_ID_PLACEHOLDER/${PROJECT_ID}/g" backend/cloudrun-gemma.yaml
sed -i "s/PROJECT_NUMBER_PLACEHOLDER/${PROJECT_NUMBER}/g" backend/cloudrun-gemma.yaml
gcloud run services replace backend/cloudrun-gemma.yaml --region=southamerica-east1
```

---

## 📚 References
* [Google Cloud Run: Mount Cloud Storage volumes](https://cloud.google.com/run/docs/configuring/services/cloud-storage-volume-mounts)
* [Google Cloud Storage: Creating buckets](https://cloud.google.com/storage/docs/creating-buckets)
* [Google Cloud Architecture Framework: AI and Machine Learning](https://cloud.google.com/architecture/framework/system-design/ai-ml)
