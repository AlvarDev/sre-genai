# Operational & Database Administration Scripts (`scripts`)

## Overview

Standalone PEP 723 (`uv run`) Python operational utilities for seeding the Firestore product catalog, simulating and cleaning up off-topic vector database drift for SRE chaos/observability exercises, and administering Firebase Authentication Role-Based Access Control (RBAC) custom claims. The static dataset `image_data_with_embeddings.csv` is treated strictly as a local data input artifact and excluded from source symbol contracts.

## Interface

- **[`seed_db.py`](./seed_db.py)**
  - `[scripts/seed_db.py:project_id]`, `[scripts/seed_db.py:database_id]`: Module-level strings resolved at import time from required environment variables `PROJECT_ID` and `FIRESTORE_DATABASE`.
  - `[scripts/seed_db.py:db]`: Module-level `google.cloud.firestore.Client(project=project_id, database=database_id)` client.
  - `[scripts/seed_db.py:generate_embeddings_and_seed]`: `generate_embeddings_and_seed() -> None` — Loads pre-computed product records and vector embeddings from `./image_data_with_embeddings.csv` and batch-writes them into the `products` Firestore collection (invoked directly via `__main__`, no CLI flags).
- **[`inject_drift.py`](./inject_drift.py)**
  - `[scripts/inject_drift.py:project_id]`, `[scripts/inject_drift.py:database_id]`: Module-level strings resolved at import time from required environment variables `PROJECT_ID` and `FIRESTORE_DATABASE`.
  - `[scripts/inject_drift.py:db]`: Module-level `google.cloud.firestore.Client(project=project_id, database=database_id)` client.
  - `[scripts/inject_drift.py:grocery_items]`: Module-level list of two off-topic synthetic product dictionaries (`parent_sku`: `'organic-potatoes'` and `'fresh-bananas'`).
  - `[scripts/inject_drift.py:inject_database_drift]`: `inject_database_drift() -> None` — Generates 768-dimensional semantic embeddings via Vertex AI (`gemini-embedding-2`) and upserts `grocery_items` into `products/{parent_sku}`.
  - `[scripts/inject_drift.py:remove_database_drift]`: `remove_database_drift() -> None` — Deletes `products/organic-potatoes` and `products/fresh-bananas` from Firestore if present.
  - `[scripts/inject_drift.py:__main__]`: Interactive `stdin` menu (`1` to inject drift, `2` to remove drift, followed by `y/N` confirmation; no `argparse` flags).
- **[`manage_admin_claims.py`](./manage_admin_claims.py)**
  - `[scripts/manage_admin_claims.py:init_firebase]`: `init_firebase(project_id: str) -> None` — Initializes the `firebase_admin` SDK app for `project_id` if `firebase_admin._apps` is empty.
  - `[scripts/manage_admin_claims.py:manage_claims]`: `manage_claims(project_id: str, email: str, grant: bool = False, revoke: bool = False) -> None` — Looks up a Firebase Auth user by email, grants or revokes the `sre_genai_admin` custom claim, and prints refreshed profile/claim metadata.
  - `[scripts/manage_admin_claims.py:main]`: `main() -> None` — `argparse` CLI entrypoint accepting `--project-id` (required `str`), `--email` (required `str`), and mutually exclusive flags `--grant`, `--revoke`, or `--list`.
- **Subdirectories**: None.

## Invariants

- `[scripts/seed_db.py:project_id]`, `[scripts/seed_db.py:database_id]`, `[scripts/inject_drift.py:project_id]`, `[scripts/inject_drift.py:database_id]`: Both `PROJECT_ID` and `FIRESTORE_DATABASE` environment variables must be set and non-empty before importing or executing either script; otherwise a `RuntimeError` is raised immediately at module import time.
- `[scripts/seed_db.py:generate_embeddings_and_seed]`: Firestore `WriteBatch` commits are bounded at `500` `batch.set` operations per commit (`batch_count >= 500`), preserving Firestore's per-batch write limit. Rows whose `image_embeddings` JSON fails to parse are skipped with a warning, and empty `retail_price` values default to `0.0`.
- `[scripts/inject_drift.py:inject_database_drift]`: Drift vectors are generated with Vertex AI model `'gemini-embedding-2'` in location `'us'` using `EmbedContentConfig(output_dimensionality=768)` and stored as `google.cloud.firestore_v1.vector.Vector` under field `'image_embeddings'` to match the `products` collection vector schema.
- `[scripts/inject_drift.py:__main__]`: Interactive execution requires explicit `'y'` (case-insensitive) confirmation before invoking `inject_database_drift()` or `remove_database_drift()`.
- `[scripts/manage_admin_claims.py:main]`: `--grant`, `--revoke`, and `--list` form a mutually exclusive `argparse` group; `--project-id` and `--email` are mandatory and stripped of surrounding whitespace.
- `[scripts/manage_admin_claims.py:manage_claims]`: The target user must already exist in Firebase Authentication (`auth.get_user_by_email(email)`), having signed in at least once; missing users or SDK failures terminate the process with `sys.exit(1)`. Granting (`claims["sre_genai_admin"] = True`) or revoking (`claims.pop("sre_genai_admin")`) preserves any unrelated keys already present in `user.custom_claims`.

## Side Effects

- `[scripts/seed_db.py:db]`, `[scripts/inject_drift.py:db]`: Instantiates a live `google.cloud.firestore.Client` at module import time.
- `[scripts/seed_db.py:generate_embeddings_and_seed]`: Reads `./image_data_with_embeddings.csv` from disk via `csv.DictReader` and performs batched Firestore `set` upserts into `products/{parent_sku}` (populating `parent_sku`, `parent_description`, `title`, `retail_price`, `img_url`, `seo_url`, `shortdesc`, `longdesc`, `keywords`, `metadescription`, `file_path`, `gcs_path`, `combined_text`, and `image_embeddings`).
- `[scripts/inject_drift.py:inject_database_drift]`: Makes outbound Vertex AI `embed_content` network calls (`google.genai.Client(vertexai=True, project=project_id, location="us")`) and overwrites Firestore documents `products/organic-potatoes` and `products/fresh-bananas`.
- `[scripts/inject_drift.py:remove_database_drift]`: Reads (`doc_ref.get()`) and deletes (`doc_ref.delete()`) Firestore documents `products/organic-potatoes` and `products/fresh-bananas`.
- `[scripts/inject_drift.py:__main__]`: Blocks on interactive `stdin` (`input()`) and logs status output to `stdout`.
- `[scripts/manage_admin_claims.py:init_firebase]`, `[scripts/manage_admin_claims.py:manage_claims]`: Initializes the global `firebase_admin` application state, performs outbound Firebase Auth Admin API reads/writes (`auth.get_user_by_email`, `auth.set_custom_user_claims`, `auth.get_user`), writes diagnostics to `stdout`/`stderr`, and exits with status code `1` on initialization or lookup errors.

## Verification

- Run: `uv run --directory backend python -m py_compile ../scripts/seed_db.py ../scripts/inject_drift.py ../scripts/manage_admin_claims.py`
