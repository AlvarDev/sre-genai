# ADR 003: Multi-Container Sidecar Architecture for Gemma 4 In-Memory Serving

## Status
Accepted & Implemented (2026-09-04)

## Context & Problem Statement
To benchmark self-hosted compute against Google Managed APIs for the Google Store Multimodal Assistant, we needed to run **Gemma 4 E2B** (`unsloth/gemma-4-E2B-it-GGUF` Q4_K_M, 2.89 GiB) under realistic production constraints:
1. Self-hosted compute must run on **Google Cloud Run** in `southamerica-east1` (no Vertex AI Model Garden).
2. Local development and rapid iteration must be supported on **Minikube** using Skaffold.
3. Container images must remain **lightweight and secure** adhering to strict developer rules (multi-stage builds, distroless/minimal bases, no multi-gigabyte layers).

---

## Architectural Decisions

### 1. Multi-Container Sidecar Pattern
- **Decision**: Decouple the application orchestrator (`backend-service`, ~150 MB FastAPI app) from the C++ inference engine (`llama-server`, ~70 MB).
- **Rationale**:
  - Eliminates rebuilding or pushing 3+ GB Docker images whenever application code or prompts change.
  - Enables independent scaling, telemetry collection, and runtime configuration.
  - Keeps the container image size well within container best practices.

### 2. Storage & Volume Mounting Strategy
- **Production (Google Cloud Run)**:
  - Mounted bucket `gs://sre-demos-files` at `/models` using Cloud Run's managed Cloud Storage FUSE driver (`gcsfuse.run.googleapis.com`).
- **Local Development (Minikube)**:
  - Copied model weights directly to Minikube's local ext4 block storage (`/var/models/gemma-4-E2B-it-Q4_K_M.gguf`) mounted via `hostPath`.
- **Key Finding & Problem Solved**:
  - Initially, `minikube mount` was tested over the Plan 9 (9P) network protocol.
  - Kernel thread profiling (`/proc/1/task/<id>/wchan`) revealed that `mmap` demand-paging caused worker threads to spend >90% of their execution time suspended in `p9_client_rpc` waiting for 4 KB network read round-trips over the host-guest loopback socket.
  - Switching Minikube to native ext4 block storage (`/var/models`) increased I/O throughput from ~4 MB/s to >500 MB/s, eliminating the bottleneck.

### 3. In-Memory Execution via `--load-mode none`
- **Decision**: Disallow default `mmap` demand paging in both environments by specifying `--load-mode none` (canonical replacement for deprecated `--no-mmap`).
- **Rationale**:
  - **Cold Start**: On container startup, `llama-server` performs a single, high-speed sequential `fread()` of the 2.89 GiB file into allocated RAM (taking ~4-6s over GCS intra-region network, ~2-3s on ext4).
  - **Inference Latency**: All token generation runs 100% in physical RAM with zero disk or GCS reads.
  - **Cost Reduction**: Eliminates thousands of billable Google Cloud Storage Class B HTTP Range requests (`GET Range: bytes=X-Y`) per chat conversation.

### 4. Runtime Parameters & KV Cache Right-Sizing
- **Context Window (`-c 4096`)**: Gemma 4 defaults to a 131,072-token context window. Without `-c`, `llama-server` allocates a massive KV cache, exhausting CPU memory bandwidth. Capping context to 4,096 tokens dramatically improves generation speed.
- **Parallel Slots (`-np 1`)**: Pinned to a single slot to guarantee predictable compute and latency without multi-slot KV contention.
- **Reasoning Flag (`--reasoning off`)**: Replaced deprecated `--chat-template-kwargs '{"enable_thinking":false}'` with `--reasoning off` to prevent thought tokens from polluting multi-turn conversational state.

### 5. OpenTelemetry Metric Collision Prevention
- **Problem**: Both `backend-gemini` and `backend-gemma` exported metrics to Google Cloud Monitoring under the `generic_node` monitored resource. Because both services wrote to identical metric descriptors simultaneously, GCM rejected time series updates with HTTP 400 `FailedPrecondition` collisions.
- **Fix**: Configured explicit OpenTelemetry `Resource` attributes (`service.name` and `service.instance.id`) in `backend/config.py`. Set `SERVICE_NAME: backend-gemini` and `SERVICE_NAME: backend-gemma` in Kubernetes manifests.

### 6. OpenAI Client Authentication Compatibility
- **Problem**: Google ADK / LiteLLM interfaces with `llama-server` via the `openai` Python SDK. The client raised `OpenAIError: Missing credentials` even when targeting local endpoints.
- **Fix**: Configured `api_key="local"` on `LiteLlm` when invoking custom `INFERENCE_ENDPOINT`.

### 7. Minikube Resource Sizing
- **Problem**: Minikube was initially created with 2 vCPUs and 4000 MB RAM. Running the K8s control plane (~1.5 GiB) alongside in-memory Gemma 4 (~3.0 GiB) saturated memory at 99.98%, triggering exit code 137 (`OOMKilled`) and freezing `kube-apiserver`.
- **Fix**: Updated Minikube Docker cgroups via `docker update --cpus 6 --memory 7200m --memory-swap 7200m minikube`, aligning with Docker Desktop's available hardware (8 CPUs, 8 GB RAM).

---

## References
- [Google Cloud Run: Mount Cloud Storage volumes](https://cloud.google.com/run/docs/configuring/services/cloud-storage-volume-mounts)
- [Google Cloud Storage FUSE Best Practices for AI/ML](https://cloud.google.com/storage/docs/gcs-fuse/ml-workloads)
- [Cloud Run Container Contract](https://cloud.google.com/run/docs/reference/container-contract)
- [Google Cloud Run Pricing](https://cloud.google.com/run/pricing)
