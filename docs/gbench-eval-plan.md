# ⚡ `gbench` Evaluation Plan: Google Store Assistant
### Comparing Gemini 3.7 Flash (Cloud Agent Platform) vs. Gemma 4 (Self-Hosted Compute)

---

## 🎯 Executive Overview

This evaluation plan benchmarks the **Google Store Multimodal Virtual Assistant**—an enterprise demonstration platform combining Multimodal RAG (`gemini-embedding-2`), Model Context Protocol (`FastMCP` over SSE), dual-layer guardrails, and Site Reliability Engineering (SRE) observability on Google Cloud Run.

The primary objective is to conduct a rigorous comparison between two architecture patterns:
1. **Managed Cloud API**: `Gemini 3.7 Flash` via **Google Agent Platform**.
2. **Self-Hosted Compute**: `Gemma 4` hosted on Cloud Run.

---

## 🏛️ System Architecture Context

When processing an end-user request, the assistant executes a **3-step sequential LLM pipeline**:

```
 [User Request] ──> (1) Pre-LLM Guardrail (Jailbreak Audit)
                          │
                          ▼
                    (2) Core Agent Orchestrator ──> [MCP Catalog Search (Firestore)]
                          │
                          ▼
                    (3) Post-RAG Guardrail (Product Drift Audit) ──> [Final Answer]
```

To isolate application overhead (guardrails + MCP vector search) from raw model serving performance, the evaluation is hosted across **2 Cloud Run backend services** exposing path-based routes (`/v1` for Full Pipeline vs. `/v1/core` for Direct Core Model).

---

## 🛠️ Microservice Test Matrix

We deploy **2 Cloud Run backend services**:

| Service ID | Host Architecture | `/v1` Path (Full Pipeline) | `/v1/core` Path (Direct Core Model) |
| :--- | :--- | :--- | :--- |
| **`backend-gemini`** | FastAPI + Gemini API (Vertex AI) | E2E System Latency (Gemini Core) | Pure TTFT/TPOT & Golden Capabilities (Gemini 3.7 Flash) |
| **`backend-gemma`** | FastAPI + Embedded Ollama (`gemma4:e4b`) | E2E System Latency (Gemma Core) | Pure TTFT/TPOT & Golden Capabilities (Gemma 4 `gemma4:e4b`) |

### ⚙️ Cloud Run Instance Right-Sizing
To ensure a fair Total Cost of Ownership (TCO) evaluation, each Cloud Run service is right-sized to its operational footprint:

| Service ID | vCPU Allocation | Memory (RAM) | Rationale |
| :--- | :--- | :--- | :--- |
| **`backend-gemini`** | 2 vCPUs | 2 GiB | Lightweight API Gateway footprint calling external Gemini API. |
| **`backend-gemma`** | 4 vCPUs | 8 GiB | Required for local `gemma4:e4b` model weights (~3.2 GB RAM) + multithreaded CPU decoding. |

> [!NOTE]
> Holding the `GUARDRAIL_MODEL` constant (`gemini-3.5-flash-lite`) across Service 1 and Service 2 ensures that the **only variable changing in the full pipeline is the core LLM**, providing a clean A/B comparison of application response time.

---

## 🧪 `gbench` Execution Suite

We run `gbench` against both backend services targeting their OpenAI-compatible REST endpoints (`/v1` vs `/v1/core`):

### 1. Full Pipeline E2E Benchmarks
Focuses on end-to-end system user experience (E2EL) under realistic multi-turn guardrail and tool execution workloads.

```bash
# Test 1: Full Pipeline (Gemini Core)
gbench --remote-endpoint https://backend-gemini-....southamerica-east1.run.app/v1 \
       --serving-only \
       --results-dir ./results/01-full-pipeline-gemini

# Test 2: Full Pipeline (Gemma 4 Core)
gbench --remote-endpoint https://backend-gemma-....southamerica-east1.run.app/v1 \
       --serving-only \
       --results-dir ./results/02-full-pipeline-gemma
```

---

### 2. Direct Core Model Benchmarks (via `/v1/core`)
Focuses on pure model performance (unfiltered TTFT, TPOT, tokens/sec) and Golden Set capability invariant pass rates (`16/16 PASS`).

```bash
# Test 3: Raw Core Model (Gemini 3.7 Flash)
gbench --remote-endpoint https://backend-gemini-....southamerica-east1.run.app/v1/core \
       --serving-only \
       --golden-only \
       --results-dir ./results/03-direct-core-gemini

# Test 4: Raw Core Model (Gemma 4)
gbench --remote-endpoint https://backend-gemma-....southamerica-east1.run.app/v1/core \
       --serving-only \
       --golden-only \
       --results-dir ./results/04-direct-core-gemma
```

---

## 📊 Metrics & Decision Matrix

The generated `summary.json` result traces will be cross-analyzed across three trade-off dimensions:

1. **Serving Performance**:
   - **TTFT (Time-to-First-Token)** & **TPOT (Time-per-Output-Token)** from Services 3 & 4.
   - **End-to-End Latency (E2EL)** from Services 1 & 2.
2. **Capability Invariant Pass Rate**:
   - Golden Set pass rates on tool calling, JSON schema generation, and reasoning invariants from Services 3 & 4.
3. **Total Cost of Ownership (TCO)**:
   - Gemini 3.7 Flash pay-per-token API cost vs. Gemma 4 Cloud Run scale-to-zero compute cost.
