# Backend Service Testing Guide

This guide explains how to test the `backend-gemini` and `backend-gemma` services locally or on Cloud Run, including obtaining authentication tokens and verifying requests with `curl`.

---

### 1. Obtain a Firebase ID Token for Testing

The backend services validate Firebase ID tokens (JWTs) via the Firebase Admin SDK. You can acquire an ID token using either method:

#### Method A: Generate via Firebase Identity Toolkit REST API
Generate an anonymous user token using your project's Web API Key:

```bash
export FIREBASE_API_KEY="<YOUR_FIREBASE_WEB_API_KEY>"

curl -s -X POST -H "Content-Type: application/json" \
  -d '{"returnSecureToken": true}' \
  "https://identitytoolkit.googleapis.com/v1/accounts:signUp?key=${FIREBASE_API_KEY}" | jq -r .idToken
```

#### Method B: Copy from Running Frontend Web App
When running the Nuxt frontend, open browser Developer Tools (Network tab), filter by `chat` or `visual-search`, and copy the token from the `Authorization: Bearer <token>` request header.

---

### 2. Verify Authenticated Requests (Using Curl)

#### Step A: Query the Backend Chat Endpoint
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
