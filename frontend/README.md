# SRE GenAI - Nuxt 3 Frontend Web App

Vue 3 / Nuxt 3 frontend application presenting the Google Store Virtual Shopping Assistant.

---

## 🛠️ Features

* **Firebase Authentication & RBAC**: Authenticates users anonymously by default, and supports Google Sign-In with Custom Claims (`sre_genai_admin`) for presenter/admin mode.
* **Admin Easter Egg & Model Switcher**: Unlocked via a 7-click sequence on the Google logo, enabling a settings drawer to switch between `Gemini 3.8 Flash` and `Gemma 4 E2B`.
* **Direct Backend Communication**: Browser client issues authenticated requests directly to Cloud Run or local KinD backend endpoints with Bearer tokens.
* **Theme Customization**: Responsive dark/light themes powered by CSS tokens and Google brand palette.
* **UI Features**: Responsive horizontal product carousel, image upload picker for visual search, and checkout simulation modal.

---

## 🏗️ Architecture

* `app.vue`: Global root layout and Google color palette design tokens.
* `pages/index.vue`: Chat workspace, message history stream, product carousel rendering, visual search input bar, and admin settings drawer.
* `nuxt.config.ts`: Public runtime environment keys for Firebase and backend URLs.

---

## 🔑 Local Kubernetes Configuration

When deploying into KinD via `skaffold dev`, the pre-deploy hook in [`skaffold.yaml`](../skaffold.yaml) automatically populates `PROJECT_ID` (from `gcloud config get-value project`) and `FIREBASE_API_KEY` (fetched from Google Cloud Secret Manager secret `firebase-web-api-key`) into the `app-config` ConfigMap. No manual Kubernetes Secret creation is required.

---

## 💻 Local Frontend Development (Instant Vite HMR)

For visual and UI changes, run Nuxt natively on your machine to take advantage of sub-50ms Hot Module Replacement (HMR) without rebuilding Docker containers:

### Pre-configured Environment Profiles
Both files are pre-configured and ignored by Git:
* `.env.local`: Connects to local KinD backends (`http://localhost:8080` & `http://localhost:8081`).
* `.env.cloud.local`: Connects to live Cloud Run backends.

### Commands

* **Develop with Local KinD Backends ($0.00 compute cost):**
  ```bash
  yarn dev
  ```
  *Executes `nuxt dev --dotenv .env.local`. Requires backends running via `skaffold dev -p backends-only`.*

* **Develop with Live Cloud Run Backends (No local K8s/RAM strain):**
  ```bash
  yarn dev:cloud
  ```
  *Executes `nuxt dev --dotenv .env.cloud.local`. Connects directly to GCP services.*

