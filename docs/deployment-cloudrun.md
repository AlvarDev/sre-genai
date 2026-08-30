# Backend Service Deployment

Use the following command to build and deploy the backend container to Cloud Run with the correct environment variables, models, and telemetry settings.

## Command

```bash
gcloud builds submit --tag southamerica-east1-docker.pkg.dev/sre-demos/sre-genai/backend-service:latest ./backend && \
gcloud run deploy backend-service \
  --image southamerica-east1-docker.pkg.dev/sre-demos/sre-genai/backend-service:latest \
  --region southamerica-east1 \
  --set-env-vars="PROJECT_ID=sre-demos,MCP_SERVER_URL=https://catalog-mcp-server-1010474272420.southamerica-east1.run.app/mcp/sse,CORE_MODEL=gemini-3.5-flash,GUARDRAIL_MODEL=gemini-3.1-flash-lite" \
  --no-cpu-throttling \
  --allow-unauthenticated \
  --platform managed
```

## Key Parameters Explained

| Parameter | Type | Purpose |
| :--- | :--- | :--- |
| `CORE_MODEL` | Environment Var | The main generative model for the assistant (configured to use the flagship `gemini-3.5-flash`). |
| `GUARDRAIL_MODEL` | Environment Var | The security model performing input validation and product classification (uses the lightweight `gemini-3.1-flash-lite` for speed and low cost). |
| `MCP_SERVER_URL` | Environment Var | The endpoint of the Catalog MCP service. |
| `--no-cpu-throttling` | Flag | Keeps the CPU allocated to the container at all times. **Critical for OpenTelemetry metrics** background batch exporters to run between requests. |
| `--allow-unauthenticated` | Flag | Permits public HTTP access to the backend endpoint. |
