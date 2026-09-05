# SRE GenAI - Nuxt 3 Frontend Web App

Vue 3 / Nuxt 3 frontend application presenting the Google Store Virtual Shopping Assistant.

---

## 🛠️ Features

* **Firebase Anonymous Authentication**: Authenticates users silently and attaches Bearer tokens to backend requests.
* **Nitro Server Proxies**: Forwards `/api/chat` and `/api/visual-search` endpoints securely to backend microservices.
* **Theme Customization**: Responsive dark/light themes powered by CSS tokens and Google brand palette.
* **UI Features**: Responsive horizontal product carousel, image upload picker for visual search, and checkout simulation modal.

---

## 🏗️ Architecture

* `app.vue`: Global root layout and Google color palette design tokens.
* `pages/index.vue`: Chat workspace, message history stream, product carousel rendering, and visual search input bar.
* `server/api/chat.post.ts`: Nitro proxy to backend `/chat`.
* `server/api/visual-search.post.ts`: Nitro proxy to backend `/visual-search`.
* `nuxt.config.ts`: Public runtime environment keys for Firebase and backend URLs.

---

## 🔑 Local Development Secrets Setup

Retrieve your Firebase Web API Key from the [Firebase Console](https://console.firebase.google.com/) (Project Settings > General > Your apps) and create the Kubernetes Secret before running `skaffold dev`:

```bash
export FIREBASE_API_KEY="<YOUR_FIREBASE_WEB_API_KEY>"
export PROJECT_ID=$(gcloud config get-value project 2>/dev/null)

kubectl create secret generic frontend-env \
  --from-literal=NUXT_PUBLIC_FIREBASE_API_KEY="$FIREBASE_API_KEY" \
  --from-literal=NUXT_PUBLIC_FIREBASE_PROJECT_ID="$PROJECT_ID" \
  --from-literal=NUXT_PUBLIC_FIREBASE_AUTH_DOMAIN="${PROJECT_ID}.firebaseapp.com" \
  --dry-run=client -o yaml | kubectl apply -f -
```

---

## 💻 Local Frontend Development (Instant Vite HMR)

For visual and UI changes, run Nuxt natively on your machine to take advantage of sub-50ms Hot Module Replacement (HMR) without rebuilding Docker containers:

### Pre-configured Environment Profiles
Both files are pre-configured and ignored by Git:
* `.env.local`: Connects to local Minikube backends (`http://localhost:8080` & `http://localhost:8081`).
* `.env.cloud.local`: Connects to live Cloud Run backends.

### Commands

* **Develop with Local Minikube Backends ($0.00 compute cost):**
  ```bash
  yarn dev
  ```
  *Executes `nuxt dev --dotenv .env.local`. Requires backends running via `skaffold dev -p backends-only`.*

* **Develop with Live Cloud Run Backends (No Minikube/RAM strain):**
  ```bash
  yarn dev:cloud
  ```
  *Executes `nuxt dev --dotenv .env.cloud.local`. Connects directly to GCP services.*

