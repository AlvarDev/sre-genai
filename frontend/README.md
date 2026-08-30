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

For local Minikube development, create the Kubernetes secret before running `skaffold dev`:

```bash
kubectl create secret generic frontend-env \
  --from-literal=NUXT_PUBLIC_FIREBASE_API_KEY="YOUR_ACTUAL_FIREBASE_API_KEY" \
  --from-literal=NUXT_PUBLIC_FIREBASE_PROJECT_ID="YOUR_PROJECT_ID" \
  --from-literal=NUXT_PUBLIC_FIREBASE_AUTH_DOMAIN="YOUR_PROJECT_ID.firebaseapp.com" \
  --dry-run=client -o yaml | kubectl apply -f -
```
