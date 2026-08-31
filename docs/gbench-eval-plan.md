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

To isolate application overhead (guardrails + MCP vector search) from raw model serving performance, the evaluation is split into **4 dedicated Cloud Run services**.

---

## 🛠️ Microservice Test Matrix

We deploy **4 distinct Cloud Run backend endpoints**:

| Service ID | Architecture Scope | Core Model | Guardrail Model | Primary Evaluation Goal |
| :--- | :--- | :--- | :--- | :--- |
| **`service-1-full-gemini`** | Full Pipeline | Gemini 3.7 Flash | Gemini 3.5 Flash-Lite | System E2E Latency (Agent Platform) |
| **`service-2-full-gemma`** | Full Pipeline | Gemma 4 | Gemini 3.5 Flash-Lite | System E2E Latency (Compute) |
| **`service-3-core-gemini`** | Direct Core Model | Gemini 3.7 Flash | *None (Bypassed)* | Pure Model TTFT/TPOT & Golden Capabilities |
| **`service-4-core-gemma`** | Direct Core Model | Gemma 4 (vLLM/Ollama `/v1`) | *None (Bypassed)* | Pure Model TTFT/TPOT & Golden Capabilities |

> [!NOTE]
> Holding the `GUARDRAIL_MODEL` constant (`gemini-3.5-flash-lite`) across Service 1 and Service 2 ensures that the **only variable changing in the full pipeline is the core LLM**, providing a clean A/B comparison of application response time.

---

## 🧪 `gbench` Execution Suite

We run `gbench` against all 4 service endpoints targeting their OpenAI-compatible `/v1/chat/completions` REST interface:

### 1. Full Pipeline E2E Benchmarks (Services 1 & 2)
Focuses on end-to-end system user experience (E2EL) under realistic multi-turn guardrail and tool execution workloads.

```bash
# Test 1: Full Pipeline (Gemini Core)
gbench --remote-endpoint https://service-1-full-gemini-....southamerica-east1.run.app/v1 \
       --serving-only \
       --results-dir ./results/01-full-pipeline-gemini

# Test 2: Full Pipeline (Gemma 4 Core)
gbench --remote-endpoint https://service-2-full-gemma-....southamerica-east1.run.app/v1 \
       --serving-only \
       --results-dir ./results/02-full-pipeline-gemma
```

---

### 2. Direct Core Model Benchmarks (Services 3 & 4)
Focuses on pure model performance (unfiltered TTFT, TPOT, tokens/sec) and Golden Set capability invariant pass rates (`16/16 PASS`).

```bash
# Test 3: Raw Core Model (Gemini 3.7 Flash)
gbench --remote-endpoint https://service-3-core-gemini-....southamerica-east1.run.app/v1 \
       --serving-only \
       --golden-only \
       --results-dir ./results/03-raw-core-gemini

# Test 4: Raw Core Model (Gemma 4)
gbench --remote-endpoint https://service-4-core-gemma-....southamerica-east1.run.app/v1 \
       --serving-only \
       --golden-only \
       --results-dir ./results/04-raw-core-gemma
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
