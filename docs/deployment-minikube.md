# Local Kubernetes Development Guide (Minikube & Skaffold)

This guide details how to initialize, configure, and operate the complete Google Store Assistant microservice stack locally on **Minikube** using **Skaffold**.

---

## 💻 Hardware Requirements & Sizing Rationale

Running the full architecture locally requires sufficient memory and CPU allocation:
* **Kubernetes Control Plane (`kube-apiserver`, `etcd`, `coredns`)**: ~1.5 GiB RAM.
* **Gemma 4 In-Memory Inference Engine (`llama-server`)**: ~3.0 GiB physical RAM (`--load-mode none`).
* **Application Services (`backend-gemini`, `backend-gemma`, `catalog-mcp`, `frontend`)**: ~1.5 GiB RAM.

> [!CAUTION]
> Starting Minikube with default resource allocations (2 vCPUs, 4000 MB RAM) will saturate memory at 99.98%, triggering Linux kernel OOMKills (`exit code 137`) on the `inference-sidecar` container and causing `kube-apiserver` to freeze.

---

## 🚀 1. Cluster Initialization

Initialize Minikube with dedicated CPU/memory sizing and the **`gcp-auth`** addon:

```bash
minikube start \
  --driver=docker \
  --cpus=6 \
  --memory=7200m \
  --addons=gcp-auth
```

### Why these flags are required:
| Flag | Purpose |
| :--- | :--- |
| `--driver=docker` | Runs the Kubernetes node directly inside your host Docker daemon for minimal virtualization overhead. |
| `--cpus=6` | Allocates 4 vCPUs to `llama-server` inference threads while reserving 2 vCPUs for the OS and application services. |
| `--memory=7200m` | Provides the headroom needed to run the control plane and in-memory model without memory pressure. |
| `--addons=gcp-auth` | Automatically mounts your active host `gcloud` credentials into pods so Vertex AI, Firestore, and Cloud Monitoring calls succeed without manual service account keys. |

---

## 📦 2. Model Weights Provisioning (ext4 Block Storage)

### A. Download the Model File from Hugging Face (if not present)
The model weights (`~2.89 GiB`) are excluded from Git via `.gitignore`. Download the quantized GGUF weights directly from Hugging Face into the `models/` directory:

```bash
mkdir -p models
curl -L "https://huggingface.co/unsloth/gemma-4-E2B-it-GGUF/resolve/main/gemma-4-E2B-it-Q4_K_M.gguf" \
  -o models/gemma-4-E2B-it-Q4_K_M.gguf
```

### B. Copy Weights into Minikube Native Storage
The Gemma 4 E2B GGUF weights (`~2.89 GiB`) must be stored directly on Minikube's native ext4 filesystem.

> [!IMPORTANT]
> **Ext4 vs 9P Mounts**: Do **not** use `minikube mount` (Plan 9 network protocol). Kernel thread profiling revealed that 9P network round-trips bottleneck sequential reading to ~4 MB/s. Copying directly to Minikube's native `/var/models` ext4 storage delivers **>500 MB/s sequential read throughput**, reducing container cold-start time from 4+ minutes to under 3 seconds.

Run these commands once to create the directory and copy the model file:

```bash
# 1. Create target directory inside Minikube node
minikube ssh "sudo mkdir -p /var/models && sudo chown -R docker:docker /var/models"

# 2. Copy the GGUF model weights into Minikube's native storage
minikube cp models/gemma-4-E2B-it-Q4_K_M.gguf /var/models/gemma-4-E2B-it-Q4_K_M.gguf
```

---

## 🔑 3. Local Secrets Setup

Retrieve your Firebase Web API Key from the [Firebase Console](https://console.firebase.google.com/) (Project Settings > General > Your apps) and create the Kubernetes Secret:

```bash
export FIREBASE_API_KEY="<YOUR_FIREBASE_WEB_API_KEY>"
export PROJECT_ID=$(gcloud config get-value project 2>/dev/null)

kubectl create secret generic frontend-env \
  --from-literal=NUXT_PUBLIC_FIREBASE_API_KEY="$FIREBASE_API_KEY" \
  --from-literal=NUXT_PUBLIC_FIREBASE_PROJECT_ID="$PROJECT_ID" \
  --from-literal=NUXT_PUBLIC_FIREBASE_AUTH_DOMAIN="${PROJECT_ID}.firebaseapp.com" \
  --dry-run=client -o yaml | kubectl apply -f -
```

*(Note: The `app-config` ConfigMap containing `PROJECT_ID` is created automatically by Skaffold's pre-deploy lifecycle hook).*

---

## 🔄 4. Running the Development Loop (Skaffold)

Launch Skaffold to automatically build images, apply manifests, and establish port forwards:

```bash
skaffold dev
```

### ⚡ Fast Frontend UI Development (Hybrid Mode)
To iterate on the Nuxt frontend with instant Hot Module Replacement (HMR) without waiting for container rebuilds:

1. **Start only the backends and MCP server in Minikube:**
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
* **Catalog MCP Server**: `http://localhost:8001/mcp/sse`

---

## 🛠️ Troubleshooting

### Check Pod Status & Events
```bash
kubectl get pods -o wide
kubectl describe pod -l app=backend-gemma
```

### Verify Model Weights Inside Node
```bash
minikube ssh "ls -lh /var/models"
```

### Clean Teardown
```bash
# Tear down deployed Kubernetes resources
skaffold delete

# Stop the Minikube virtual machine when finished
minikube stop
```
