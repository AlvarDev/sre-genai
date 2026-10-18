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

All deployments run through Cloud Build triggers on every push to `main`. There is no manual deploy path: the deploy settings (flags, environment variables, IAM) live only in [`backend/cloudbuild.yaml`](../backend/cloudbuild.yaml) and [`backend/cloudrun-gemma.yaml`](../backend/cloudrun-gemma.yaml). Change them there.

For the backends, the build:

1. Builds the backend image and pushes it to Artifact Registry, tagged with the commit SHA.
2. Deploys `backend-gemini` with `gcloud run deploy`.
3. Deploys `backend-gemma` (multi-container sidecar with the GCS FUSE mount) with `gcloud run services replace`, after filling in the project placeholders in `cloudrun-gemma.yaml` inside the build workspace.

Both backends are deployed **closed**: they require a Google identity token. To open them for a live audience and close them again, follow the [talk-day runbook](talk-day-runbook.md).

`ALLOWED_ORIGINS` is required. The backend refuses to start if it is missing, empty or `*`. It must be the exact frontend URL, or the browser blocks the requests (CORS).

---

## 📚 References
* [Google Cloud Run: Mount Cloud Storage volumes](https://cloud.google.com/run/docs/configuring/services/cloud-storage-volume-mounts)
* [Google Cloud Storage: Creating buckets](https://cloud.google.com/storage/docs/creating-buckets)
* [Google Cloud Architecture Framework: AI and Machine Learning](https://cloud.google.com/architecture/framework/system-design/ai-ml)
