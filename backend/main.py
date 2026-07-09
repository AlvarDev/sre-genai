import os
import uuid
from fastapi import FastAPI, Header, HTTPException, UploadFile, File, Form
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import firebase_admin
from firebase_admin import credentials, firestore
from backend.agent.orchestrator import run_text_chat, run_visual_search
from backend.agent.guardrail import GuardrailException

# 1. Initialize Firebase Admin and Firestore Client
# Explicitly targeting our named database 'sre-genai'
if not firebase_admin._apps:
    firebase_admin.initialize_app()

db = firestore.client(database="sre-genai")

# 2. FastAPI Setup
app = FastAPI(title="SRE GenAI Agent Backend")

# Enable CORS for frontend connection (local dev and prod)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 3. Models
class ChatRequest(BaseModel):
    message: str
    session_id: str

class ChatResponse(BaseModel):
    text: str
    session_id: str

# Helper to manage chat history in Firestore
def get_session_history(session_id: str) -> list:
    try:
        doc_ref = db.collection("conversations").document(session_id)
        doc = doc_ref.get()
        if doc.exists:
            return doc.to_dict().get("messages", [])
    except Exception as e:
        print(f"Error fetching session history: {e}")
    return []

def save_session_history(session_id: str, messages: list, user_uid: str):
    try:
        doc_ref = db.collection("conversations").document(session_id)
        doc_ref.set({
            "messages": messages[-10:], # Keep only last 10 messages to optimize context size
            "user_uid": user_uid,
            "updated_at": firestore.SERVER_TIMESTAMP
        }, merge=True)
    except Exception as e:
        print(f"Error saving session history: {e}")

# 4. Endpoints
@app.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest, x_user_uid: str = Header(default="anonymous_user")):
    session_id = request.session_id or str(uuid.uuid4())
    user_query = request.message

    # Load history
    history = get_session_history(session_id)

    try:
        # Run orchestrator
        agent_reply = run_text_chat(user_query, history)
    except GuardrailException as ge:
        # If blocked by the Pre-LLM safety guardrail
        return ChatResponse(text=str(ge), session_id=session_id)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Agent execution failed: {str(e)}")

    # Update and save history
    history.append({"role": "user", "content": user_query})
    history.append({"role": "model", "content": agent_reply})
    save_session_history(session_id, history, x_user_uid)

    return ChatResponse(text=agent_reply, session_id=session_id)

@app.post("/visual-search")
async def visual_search(
    image: UploadFile = File(...),
    message: str = Form(default=""),
    session_id: str = Form(default=""),
    x_user_uid: str = Header(default="anonymous_user")
):
    active_session_id = session_id or str(uuid.uuid4())
    
    try:
        # Read uploaded image bytes
        image_bytes = await image.read()
        
        # Run visual search workflow
        search_result = run_visual_search(image_bytes, message)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Visual search failed: {str(e)}")

    # Save to session history
    history = get_session_history(active_session_id)
    history.append({"role": "user", "content": f"[Buscou por Imagem] {message}".strip()})
    history.append({"role": "model", "content": search_result["text"]})
    save_session_history(active_session_id, history, x_user_uid)

    return {
        "text": search_result["text"],
        "products": search_result["products"],
        "session_id": active_session_id
    }

@app.get("/health")
def health():
    return {"status": "healthy"}
