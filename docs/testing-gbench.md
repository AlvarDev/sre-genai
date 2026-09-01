# gbench Backend Evaluation & Comparison Guide

This document outlines the evaluation strategy for comparing **Backend Service 1 (Cloud Run + Gemini API)** against **Backend Service 2 (Cloud Run + Gemma CPU)** using `gbench`.

---

## 🎯 Test Objective

Evaluate performance (latency & throughput) and capability (tool calling & structured output accuracy) across two self-hosted microservice backends under identical execution conditions:

1. **Backend Service 1 (`backend-service`)**: Cloud Run microservice integrated with Gemini API.
2. **Backend Service 2 (`gemma-backend-service`)**: Cloud Run microservice running Gemma on vCPU without GPUs.

---

## ⚡ `gbench` Benchmark Pillars

### 1. Serving Performance Baseline (`--serving-only`)
* **TTFT (Time-to-First-Token)**: Response start latency.
* **TPOT (Time-per-Output-Token)**: Token generation speed.
* **E2EL (End-to-End Latency)**: Total request duration.
* **Output Throughput**: Tokens per second.

### 2. Golden Set Capability Smoke-Testing (`--golden-only`)
* Structured JSON schema generation
* Single & multi-tool call formatting
* Canonical code execution invariants

---

## 🛠️ Execution Commands

### Benchmark Backend 1 (Gemini Backend):
```bash
gbench --remote-endpoint https://backend-service-....southamerica-east1.run.app/v1 \
       --golden-only \
       --serving-only \
       --results-dir ./results/gemini-backend
```

### Benchmark Backend 2 (Gemma CPU Backend):
```bash
gbench --remote-endpoint https://gemma-backend-service-....southamerica-east1.run.app/v1 \
       --golden-only \
       --serving-only \
       --results-dir ./results/gemma-backend
```

---

## 📊 Trade-off Decision Matrix

Compare the resulting trace files (`summary.json`) across:
1. **Total Cost of Ownership (TCO)**: Gemini API pay-per-token vs Gemma CPU Cloud Run scale-to-zero compute.
2. **Capability Invariant Pass Rate**: Tool-calling pass rate on `--golden-only`.
3. **End-to-End Latency**: E2E response duration.
