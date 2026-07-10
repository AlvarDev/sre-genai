# Backend Service Testing Guide

This guide explains how to test the `backend-service` locally, including launching dependencies and verifying authenticated requests.

---

### 1. Start the Firebase Auth Emulator

Run this command in the root of the project to start the local Auth Emulator:

```bash
npx -y firebase-tools@latest emulators:start --only auth
```

*(Or, if you have `firebase-tools` installed globally, run: `firebase emulators:start --only auth`)*

This starts the authentication emulator on port `9099` (with the web console available at `http://localhost:4000/auth`).

---

### 2. Local Backend Service Configuration

When running inside Minikube, the backend container automatically detects the local emulator via:
*   `FIREBASE_AUTH_EMULATOR_HOST=10.0.2.2:9099`

---

### 3. Verify Authenticated Requests (Using Curl)

To test the authenticated backend endpoints (`/chat` or `/visual-search`) locally without the frontend UI, follow these steps:

#### Step A: Generate a Mock Firebase ID Token
Send an anonymous signup request directly to the local Auth Emulator:

```bash
curl -X POST -H "Content-Type: application/json" \
  -d '{"returnSecureToken": true}' \
  "http://localhost:9099/identitytoolkit.googleapis.com/v1/accounts:signUp?key=mock-api-key"
```

The response will contain the **`idToken`** (JWT):
```json
{
  "idToken": "eyJhbGciOiJSUzI1Ni...",
  "localId": "some-anonymous-uid",
  "isNewUser": true
}
```
*Copy the `idToken` value.*

#### Step B: Query the Backend Chat Endpoint
Send a POST request to the local backend `/chat` endpoint (port `8080`), passing the token in the `Authorization` header:

```bash
curl -X POST -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_ID_TOKEN_HERE" \
  -d '{"message": "Do you have hoodies?", "session_id": "test_session_123"}' \
  "http://localhost:8080/chat"
```

**Testing the Off-Topic/Potato Guardrail:**
To test how the backend handles off-topic queries or database drift validation using text:

```bash
curl -X POST -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_ID_TOKEN_HERE" \
  -d '{"message": "Você vende batatas orgânicas?", "session_id": "test_session_123"}' \
  "http://localhost:8080/chat"
```


#### Step C: Query the Backend Visual Search Endpoint
To test image-based searches with the local `hoodie-io.png` file:

```bash
curl -X POST \
  -H "Authorization: Bearer YOUR_ID_TOKEN_HERE" \
  -F "image=@hoodie-io.png" \
  -F "message=I want this but with the YouTube logo" \
  -F "session_id=test_session_123" \
  "http://localhost:8080/visual-search"
```
