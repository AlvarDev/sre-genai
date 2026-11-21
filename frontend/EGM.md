# Frontend Service (`frontend`)

## Overview
Nuxt 3 (`^3.15.0`) and Vue 3 (`^3.5.42`) web frontend package (`google-store-assistant-frontend`) for the Google Store Virtual Shopping Assistant. Provides the root application shell, global light/dark theme binding, public runtime configuration for Firebase Authentication and Gemini/Gemma Cloud Run backends, distroless Node.js 22 containerization, and Cloud Build deployment automation, while delegating the interactive chat and visual search route view to [`pages`](./pages/EGM.md).

## Interface
- **Package Manifest (`package.json`)**: Private ESM package (`"name": "google-store-assistant-frontend"`, `"private": true`, `"type": "module"`) declaring `firebase` (`^10.8.0`), `nuxt` (`^3.15.0`), `vue` (`^3.5.42`), and `vue-router` (`^4.3.0`), and exposing scripts `build` (`nuxt build`), `dev` (`nuxt dev --dotenv .env.local`), `dev:cloud` (`nuxt dev --dotenv .env.cloud.local`), `generate` (`nuxt generate`), `preview` (`nuxt preview`), `postinstall` (`nuxt prepare`), and `start` (`node .output/server/index.mjs`) (`[package.json:name]`, `[package.json:scripts]`, `[package.json:dependencies]`).
- **Nuxt Configuration (`nuxt.config.ts`)**: `defineNuxtConfig` exporting `runtimeConfig.public` keys `firebaseApiKey`, `firebaseProjectId`, `firebaseAuthDomain`, `backendGeminiUrl`, and `backendGemmaUrl` (defaulting to `""`), plus `app.head` metadata (`title: "Google Store Assistant"`, `utf-8`, viewport, description, gstatic WebP favicon, and Google Fonts `Outfit` stylesheet) (`[nuxt.config.ts:defineNuxtConfig]`, `[nuxt.config.ts:runtimeConfig.public]`, `[nuxt.config.ts:app.head]`).
- **Root Application Shell (`app.vue`)**: Initializes shared reactive state `useState('darkMode', () => true)`, binds the root `<html>` `class` attribute to `'theme-dark'` or `'theme-light'` via `useHead({ htmlAttrs })`, and mounts `<NuxtPage />` inside `.app-container` (`[app.vue:isDarkMode]`, `[app.vue:useHead]`, `[app.vue:<template>]`).
- **Container Entrypoint (`Dockerfile`)**: Exposes `PORT=3000` (`EXPOSE 3000`) and runs `CMD [".output/server/index.mjs"]` on `gcr.io/distroless/nodejs22-debian13:nonroot` (`[Dockerfile:PORT]`, `[Dockerfile:CMD]`).
- **Cloud Build Pipeline (`cloudbuild.yaml`)**: Builds, pushes, and deploys Cloud Run service `frontend-service` in `southamerica-east1` with `--allow-unauthenticated` public ingress (`[cloudbuild.yaml:build-frontend-service]`, `[cloudbuild.yaml:push-frontend-service]`, `[cloudbuild.yaml:deploy-frontend-service]`).
- **Subdirectories**:
  - [`pages`](./pages/EGM.md): Root `/` route view (`index.vue`) implementing conversational RAG, multimodal visual search, Firebase anonymous/Google RBAC authentication (`sre_genai_admin`), 7-click developer unlock, and Gemini/Gemma backend switching.

## Invariants
- **Dependency Floors**: `package.json` enforces Yarn `resolutions` for `@vue/server-renderer` (`^3.5.42`), `source-map-js` (`^1.2.2`), and `undici` (`^6.29.0`) (`[package.json:resolutions]`).
- **DevTools Disabled**: Nuxt DevTools remain disabled in configuration (`devtools: { enabled: false }`) (`[nuxt.config.ts:devtools]`).
- **Global Theme Default**: Shared state `'darkMode'` defaults to `true`, constraining root `<html>` theme classes to `'theme-dark'` or `'theme-light'` across `app.vue` and [`pages`](./pages/EGM.md) (`[app.vue:isDarkMode]`).
- **Hardened Multi-Stage Container**: `Dockerfile` builds with `node:22-alpine` using `yarn install --frozen-lockfile` and `yarn build`, copies only `/app/.output` (`--chown=0:65532`) into `gcr.io/distroless/nodejs22-debian13:nonroot`, and executes as `USER nonroot` (`[Dockerfile:builder]`, `[Dockerfile:USER]`).
- **Cloud Run Security & Scaling Controls**: `cloudbuild.yaml` deploys `frontend-service` strictly to `--region=southamerica-east1` with `--max=3`, dedicated service account `frontend-sa@$PROJECT_ID.iam.gserviceaccount.com`, explicit `NUXT_PUBLIC_*` environment variables, and Secret Manager secret binding `NUXT_PUBLIC_FIREBASE_API_KEY=firebase-web-api-key:latest` (`[cloudbuild.yaml:deploy-frontend-service]`).

## Side Effects
- **Environment Variable Resolution**: Reads `process.env.NUXT_PUBLIC_FIREBASE_API_KEY`, `NUXT_PUBLIC_FIREBASE_PROJECT_ID`, `NUXT_PUBLIC_FIREBASE_AUTH_DOMAIN`, `NUXT_PUBLIC_BACKEND_GEMINI_URL`, and `NUXT_PUBLIC_BACKEND_GEMMA_URL` in `nuxt.config.ts` (`[nuxt.config.ts:runtimeConfig.public]`).
- **Document Head & External Asset Loads**: Mutates `<html class="...">` reactively via `useHead` in `app.vue` and instructs client browsers to load favicon and font stylesheets from `https://www.gstatic.com` and `https://fonts.googleapis.com` (`[app.vue:useHead]`, `[nuxt.config.ts:app.head.link]`).
- **CI/CD Artifact & Cloud Run Mutations**: When executed via Cloud Build, builds and pushes `southamerica-east1-docker.pkg.dev/$PROJECT_ID/sre-genai/frontend-service` (`:$COMMIT_SHA` and `:latest`), updates Cloud Run service `frontend-service`, and mounts Secret Manager version `firebase-web-api-key:latest` (`[cloudbuild.yaml:steps]`).
- **Route-Level Runtime Side Effects**: Through [`pages`](./pages/EGM.md), performs Firebase client authentication, authenticated `POST /chat` and `POST /visual-search` requests against the configured Gemini/Gemma backend URLs, clipboard writes, `FileReader` image reads, and DOM scroll/focus updates.

## Verification
- Run: `yarn --cwd frontend build`
