# Catalog MCP Server Testing Guide

This guide details how to manually test `catalog-mcp-service` locally when running in Kubernetes (KinD).

---

### Step 0: Ensure the Firestore Vector Index is Created

Before running vector queries, make sure the required vector index is created on the `sre-genai` database:

```bash
gcloud firestore indexes composite create --project=sre-demos --database="sre-genai" --collection-group=products --query-scope=COLLECTION --field-config=vector-config='{"dimension":"768","flat": "{}"}',field-path=image_embeddings
```
*(This setup takes about 2 to 5 minutes to become active).*

---

### Terminal 1
Forward the internal service port `8001` to local port `8002` on your host:
```bash
kubectl port-forward svc/catalog-mcp-service 8002:8001
```

---

### Terminal 2
Because `catalog-mcp` runs in stateless Streamable HTTP mode at `/mcp/`, each JSON-RPC 2.0 `POST` request is independent and returns its JSON response directly (no session ID or separate SSE stream required).

#### Step 1: List the available tools (`tools/list`)
```bash
curl -X POST http://127.0.0.1:8002/mcp/ \
  -H "Content-Type: application/json" \
  -H "Accept: application/json, text/event-stream" \
  -d '{"jsonrpc": "2.0", "id": 1, "method": "tools/list", "params": {}}'
```

#### Step 2: Execute a semantic catalog search (`tools/call`)
```bash
curl -X POST http://127.0.0.1:8002/mcp/ \
  -H "Content-Type: application/json" \
  -H "Accept: application/json, text/event-stream" \
  -d '{"jsonrpc": "2.0", "id": 2, "method": "tools/call", "params": {"name": "search_catalog", "arguments": {"query_text": "moletom"}}}'
```
