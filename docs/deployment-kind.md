# Local Kubernetes Development Guide (KinD, Podman & Skaffold)

This guide details how to initialize, configure, and operate the complete Google Store Assistant microservice stack locally on **KinD (Kubernetes in Docker/Podman)** using **Rootless Podman**, **Workload Identity Federation (WIF)**, and **Skaffold**.

---

## 💻 Hardware Requirements & Sizing Rationale

Running the full architecture locally requires sufficient memory and CPU allocation:
* **Kubernetes Control Plane (`kube-apiserver`, `etcd`, `coredns`)**: ~1.5 GiB RAM.
* **Gemma 4 In-Memory Inference Engine (`llama-server`)**: ~3.0 GiB physical RAM (`--load-mode none`).
* **Application Services (`backend-gemini`, `backend-gemma`, `catalog-mcp`, `frontend`)**: ~1.5 GiB RAM.

---

## 🚀 1. Cluster Initialization (KinD + Podman)

Create the local `gstore-cluster` KinD cluster using the Podman provider:

```bash
KIND_EXPERIMENTAL_PROVIDER=podman kind create cluster --name gstore-cluster
```

> [!IMPORTANT]
> **Zero Host Credential Mounts**: Do **not** mount `~/.config/gcloud` or service account keys into the KinD node. Pods authenticate to Google Cloud using short-lived projected Kubernetes ServiceAccount tokens via **Workload Identity Federation**.

---

## 🔐 2. Workload Identity Federation Setup (One-Time per GCP Project)

The `backend-gemini`, `backend-gemma`, and `catalog-mcp` pods authenticate directly to Google Cloud APIs using their Kubernetes ServiceAccounts (`backend-sa` and `catalog-mcp-sa`) via Workload Identity Federation direct resource access.

### A. Enable Required APIs
```bash
export PROJECT_ID=$(gcloud config get-value project 2>/dev/null)

gcloud services enable \
  iam.googleapis.com \
  cloudresourcemanager.googleapis.com \
  iamcredentials.googleapis.com \
  sts.googleapis.com \
  --project="$PROJECT_ID"
```

### B. Create the Workload Identity Pool & OIDC Provider
Extract the cluster's OIDC issuer URI and public JSON Web Key Set (JWKS), then register the cluster as an OIDC provider with an attribute condition restricting access strictly to `backend-sa` and `catalog-mcp-sa`:

```bash
ISSUER=$(kubectl get --raw /.well-known/openid-configuration | jq -r .issuer)
kubectl get --raw /openid/v1/jwks > /tmp/cluster-jwks.json

gcloud iam workload-identity-pools create local-kind \
  --location="global" \
  --description="Local KinD cluster for sre-genai" \
  --display-name="local-kind" \
  --project="$PROJECT_ID"

gcloud iam workload-identity-pools providers create-oidc gstore-cluster \
  --location="global" \
  --workload-identity-pool="local-kind" \
  --issuer-uri="$ISSUER" \
  --attribute-mapping="google.subject=assertion.sub,attribute.namespace=assertion['kubernetes.io']['namespace'],attribute.service_account_name=assertion['kubernetes.io']['serviceaccount']['name'],attribute.pod=assertion['kubernetes.io']['pod']['name']" \
  --attribute-condition="assertion.sub in ['system:serviceaccount:default:backend-sa','system:serviceaccount:default:catalog-mcp-sa']" \
  --jwk-json-path="/tmp/cluster-jwks.json" \
  --project="$PROJECT_ID"

rm -f /tmp/cluster-jwks.json
```

### C. Grant Direct IAM Roles to Kubernetes ServiceAccounts
Workload Identity Federation principal identifiers require the **GCP project number** (configured as `1010474272420` for `sre-demos`):

```bash
export PROJECT_NUMBER=$(gcloud projects describe "$PROJECT_ID" --format="value(projectNumber)")

# Grant roles to backend-sa (Vertex AI, Cloud Trace, Firestore, Cloud Monitoring)
for ROLE in roles/aiplatform.user roles/cloudtrace.agent roles/datastore.user roles/monitoring.metricWriter; do
  gcloud projects add-iam-policy-binding "projects/${PROJECT_ID}" \
    --role="$ROLE" \
    --member="principal://iam.googleapis.com/projects/${PROJECT_NUMBER}/locations/global/workloadIdentityPools/local-kind/subject/system:serviceaccount:default:backend-sa" \
    --condition=None
done

# Grant roles to catalog-mcp-sa (Vertex AI embeddings, Cloud Trace, Firestore)
for ROLE in roles/aiplatform.user roles/cloudtrace.agent roles/datastore.user; do
  gcloud projects add-iam-policy-binding "projects/${PROJECT_ID}" \
    --role="$ROLE" \
    --member="principal://iam.googleapis.com/projects/${PROJECT_NUMBER}/locations/global/workloadIdentityPools/local-kind/subject/system:serviceaccount:default:catalog-mcp-sa" \
    --condition=None
done
```

> [!NOTE]
> **Using a Different GCP Project**: The Kubernetes manifests (`k8s/backend-gemini.yaml`, `k8s/backend-gemma.yaml`, `k8s/catalog-mcp.yaml`) and `skaffold.yaml` reference project number `1010474272420` (`sre-demos`) in the WIF provider path. If you deploy against a different project, replace `1010474272420` with your project number in those four files.

### D. Updating JWKS After Recreating the KinD Cluster
Whenever you delete and recreate the `gstore-cluster` KinD cluster, Kubernetes generates a new OIDC signing keypair. Upload the new JWKS so Google Cloud STS continues accepting pod tokens:

```bash
kubectl get --raw /openid/v1/jwks > /tmp/cluster-jwks.json
gcloud iam workload-identity-pools providers update-oidc gstore-cluster \
  --workload-identity-pool="local-kind" \
  --location="global" \
  --jwk-json-path="/tmp/cluster-jwks.json" \
  --project="$PROJECT_ID"
rm -f /tmp/cluster-jwks.json
```

---

## 📦 3. Model Weights Provisioning (Node ext4 Storage)

### A. Download the Model File from Hugging Face (if not present)
The model weights (`~2.89 GiB`) are excluded from Git via `.gitignore`. Download the quantized GGUF weights directly from Hugging Face into the `models/` directory:

```bash
mkdir -p models
curl -L "https://huggingface.co/unsloth/gemma-4-E2B-it-GGUF/resolve/main/gemma-4-E2B-it-Q4_K_M.gguf" \
  -o models/gemma-4-E2B-it-Q4_K_M.gguf
```

### B. Copy Weights into the KinD Node Container
Copy the GGUF file into `/var/models` inside `gstore-cluster-control-plane` and set ownership to UID/GID `65532:65532` (`0640`) so the Distroless `nonroot` `inference-sidecar` container can read it:

```bash
# 1. Create target directory inside the KinD control-plane node
podman exec gstore-cluster-control-plane mkdir -p /var/models

# 2. Copy the GGUF model weights and set nonroot permissions (65532:65532)
podman cp models/gemma-4-E2B-it-Q4_K_M.gguf gstore-cluster-control-plane:/var/models/gemma-4-E2B-it-Q4_K_M.gguf
podman exec gstore-cluster-control-plane chown -R 65532:65532 /var/models
podman exec gstore-cluster-control-plane chmod 0640 /var/models/gemma-4-E2B-it-Q4_K_M.gguf
```

---

## 🔄 4. Running the Development Loop (Skaffold)

Skaffold's pre-deploy `before` hook in [`skaffold.yaml`](../skaffold.yaml) automatically provisions two out-of-Git ConfigMaps before deploying manifests:
1. **`app-config`**: Populated with `PROJECT_ID` (from `gcloud config get-value project`) and `FIREBASE_API_KEY` (fetched from Secret Manager secret `firebase-web-api-key`).
2. **`workload-identity-credential-configuration`**: Generated dynamically via `gcloud iam workload-identity-pools create-cred-config` using a temporary file.

Launch Skaffold to build images with Podman, load them into KinD, apply manifests, and establish port forwards:

```bash
skaffold dev
```

### ⚡ Fast Frontend UI Development (Hybrid Mode)
To iterate on the Nuxt frontend with instant Hot Module Replacement (HMR) without waiting for container rebuilds:

1. **Start only the backends and MCP server in KinD:**
   ```bash
   skaffold dev -p backends-only
   ```
   *(Leaves port 3000 unallocated and forwards Gemini to `localhost:8080` and Gemma to `localhost:8081`).*

2. **Start the Nuxt dev server natively on your host:**
   ```bash
   cd frontend && yarn dev
   ```

### Local Access Endpoints:
* **Frontend Web Application**: [http://localhost:3000](http://localhost:3000)
* **Gemini Agent Backend**: [http://localhost:8080](http://localhost:8080) (`/docs` for Swagger UI)
* **Gemma Agent Backend**: [http://localhost:8081](http://localhost:8081) (`/docs` for Swagger UI)
* **Catalog MCP Server**: `http://localhost:8001/mcp/` (Streamable HTTP)

---

## 🛠️ Troubleshooting

### Check Pod Status & Events
```bash
kubectl get pods -o wide
kubectl describe pod -l app=backend-gemma
```

### Verify Workload Identity Federation Token Exchange Inside a Pod
```bash
kubectl exec deploy/backend-gemini-deployment -- python -c \
  "import google.auth, google.auth.transport.requests as r; c,p=google.auth.default(scopes=['https://www.googleapis.com/auth/cloud-platform']); c.refresh(r.Request()); print(type(c).__name__, p, bool(c.token))"
```

### Verify Model Weights Inside Node
```bash
podman exec gstore-cluster-control-plane ls -lh /var/models
```

### Clean Teardown
```bash
# Tear down deployed Kubernetes resources
skaffold delete
```
