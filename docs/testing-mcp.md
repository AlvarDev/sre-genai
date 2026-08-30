# Catalog MCP Server Testing Guide

This guide details how to manually test the `catalog-mcp-service` locally when running in Minikube.

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
Listen to the Server-Sent Events (SSE) stream to receive response payloads:
```bash
curl -N -H "Accept: text/event-stream" http://localhost:8002/mcp/sse
```
*Note: Copy the `session_id` from the output (e.g. `session_id=YOUR_SESSION_ID`).*

---

### Terminal 3

Execute the following commands sequentially to perform the protocol handshake and run queries:

#### Step 1: Send the `initialize` request
First, initialize the session with the server's protocol version:
```bash
curl -X POST -H "Content-Type: application/json" \
  -d '{"jsonrpc": "2.0", "id": 1, "method": "initialize", "params": {"protocolVersion": "2024-11-05", "capabilities": {}, "clientInfo": {"name": "curl-client", "version": "1.0.0"}}}' \
  "http://localhost:8002/mcp/messages/?session_id=YOUR_SESSION_ID_HERE"
```

#### Step 2: Send the `initialized` notification
Next, tell the server that the handshake is complete:
```bash
curl -X POST -H "Content-Type: application/json" \
  -d '{"jsonrpc": "2.0", "method": "notifications/initialized"}' \
  "http://localhost:8002/mcp/messages/?session_id=YOUR_SESSION_ID_HERE"
```

#### Step 3: Now list the tools!
Now that the initialization handshake is complete, you can successfully request the list of tools:
```bash
curl -X POST -H "Content-Type: application/json" \
  -d '{"jsonrpc": "2.0", "method": "tools/list", "params": {}, "id": 2}' \
  "http://localhost:8002/mcp/messages/?session_id=YOUR_SESSION_ID_HERE"
```

#### Step 4: Now query!
Send a text-to-image semantic search query (e.g. "organic"):
```bash
curl -X POST -H "Content-Type: application/json" \
  -d '{"jsonrpc": "2.0", "method": "tools/call", "params": {"name": "search_catalog", "arguments": {"query_text": "organic"}}, "id": 2}' \
  "http://localhost:8002/mcp/messages/?session_id=YOUR_SESSION_ID_HERE"
```
*(All responses will print in **Terminal 2**).*
