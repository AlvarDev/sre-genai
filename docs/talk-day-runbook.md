# Talk-day runbook

Steps to open the demo to a live audience and close it again afterwards.

The backends (`backend-gemini`, `backend-gemma`) are deployed **closed**: they require a Google identity token, so browser requests fail with `403` until you open them. Opening and closing is done by hand, here, so a normal deploy can never leave them public by accident.

All services run in `southamerica-east1`. Commands assume `gcloud config set project <PROJECT_ID>` was run first.

> [!IMPORTANT]
> `backend-gemini` and `catalog-mcp-server` must run the same release: the backend talks to the catalog at `/mcp/` (stateless Streamable HTTP). Roll them back **together** (see [If something fails](#if-something-fails)).

> [!WARNING]
> Do not push to `main` from T-30 until the backend is closed again. Every push triggers Cloud Build, and the `backend-gemini` deploy runs with `--no-allow-unauthenticated`, which removes the `allUsers` grant and closes the backend in the middle of the talk.

## One time only: after the first deploy of this release

Earlier versions of `backend/cloudbuild.yaml` granted `allUsers` on `backend-gemma` in every build. That step is gone, but removing it does not revoke the grant that already exists. Remove it once:

```bash
gcloud run services remove-iam-policy-binding backend-gemma \
  --region=southamerica-east1 --member=allUsers --role=roles/run.invoker
```

**Verify:** `gcloud run services get-iam-policy backend-gemma --region=southamerica-east1` shows **no** `allUsers`. Do the same check for `backend-gemini`.

## T-30 min: keep instances warm

```bash
gcloud run services update backend-gemini --region=southamerica-east1 --min=2
gcloud run services update catalog-mcp-server --region=southamerica-east1 --min=2
```

**Verify:** each service shows `run.googleapis.com/minScale: '2'`:

```bash
gcloud run services describe backend-gemini --region=southamerica-east1 --format="yaml(metadata.annotations)"
gcloud run services describe catalog-mcp-server --region=southamerica-east1 --format="yaml(metadata.annotations)"
```

## T-20 min: open the backend

```bash
gcloud run services add-iam-policy-binding backend-gemini \
  --region=southamerica-east1 --member=allUsers --role=roles/run.invoker
```

Only if you will demo Gemma (admin users):

```bash
gcloud run services add-iam-policy-binding backend-gemma \
  --region=southamerica-east1 --member=allUsers --role=roles/run.invoker
```

**Verify:** `allUsers` appears with `roles/run.invoker`:

```bash
gcloud run services get-iam-policy backend-gemini --region=southamerica-east1
```

The app still requires a valid Firebase ID token on every request; opening Cloud Run IAM only lets browsers reach the service.

## T-15 min: warm-up

1. Open the frontend URL on your phone and send 3 messages (one with an image).
2. Watch the dashboard: data should appear within about 45 s (metrics are exported every 15 s).

**Verify:** the "Token Consumption Rate" chart shows new points, and Cloud Logging shows no `ERROR` entries for `backend-gemini` or `catalog-mcp-server`.

**URL to share with the audience:** exactly `https://frontend-service-<PROJECT_NUMBER>.southamerica-east1.run.app`. The backend's CORS setting (`ALLOWED_ORIGINS`) allows only this origin, so the other URL Cloud Run shows for the same service (or a custom domain) will fail in the browser.

## After the talk: close everything

```bash
gcloud run services remove-iam-policy-binding backend-gemini \
  --region=southamerica-east1 --member=allUsers --role=roles/run.invoker
# Only if you opened it:
gcloud run services remove-iam-policy-binding backend-gemma \
  --region=southamerica-east1 --member=allUsers --role=roles/run.invoker

gcloud run services update backend-gemini --region=southamerica-east1 --min=default
gcloud run services update catalog-mcp-server --region=southamerica-east1 --min=default
```

**Verify:**

- `gcloud run services get-iam-policy backend-gemini --region=southamerica-east1` shows **no** `allUsers` (same for `backend-gemma`).
- `run.googleapis.com/minScale` is gone from both services (`describe` command above).
- An unauthenticated request is rejected:

  ```bash
  curl -s -o /dev/null -w "%{http_code}\n" https://backend-gemini-<PROJECT_NUMBER>.southamerica-east1.run.app/health
  ```

  Expected: `403`.

## If something fails

Find the previous working revisions:

```bash
gcloud run revisions list --service=backend-gemini --region=southamerica-east1
gcloud run revisions list --service=catalog-mcp-server --region=southamerica-east1
```

Roll **both** back together (the backend and the catalog must agree on the MCP transport):

```bash
gcloud run services update-traffic catalog-mcp-server --region=southamerica-east1 --to-revisions=<PREVIOUS_CATALOG_REVISION>=100
gcloud run services update-traffic backend-gemini --region=southamerica-east1 --to-revisions=<PREVIOUS_BACKEND_REVISION>=100
```

If you demo Gemma, roll `backend-gemma` back too; it also calls the catalog at `/mcp/`:

```bash
gcloud run revisions list --service=backend-gemma --region=southamerica-east1
gcloud run services update-traffic backend-gemma --region=southamerica-east1 --to-revisions=<PREVIOUS_GEMMA_REVISION>=100
```

To return to the latest revision later:

```bash
gcloud run services update-traffic backend-gemini --region=southamerica-east1 --to-latest
gcloud run services update-traffic catalog-mcp-server --region=southamerica-east1 --to-latest
# Only if you rolled it back:
gcloud run services update-traffic backend-gemma --region=southamerica-east1 --to-latest
```

## Recommended (outside this repo)

- A **budget alert** on the billing account, set before the talk. It is a billing setting, so it is not managed here.
