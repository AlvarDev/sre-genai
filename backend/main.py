import os
import uuid
from fastapi import FastAPI, Header, HTTPException, UploadFile, File, Form, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel
import firebase_admin
from firebase_admin import credentials, firestore, auth
from agent.orchestrator import run_text_chat, run_visual_search
from agent.guardrail import GuardrailException

# Initialize OpenTelemetry Metrics with Google Cloud Monitoring Exporter
from opentelemetry import metrics
from opentelemetry.sdk.metrics import MeterProvider
from opentelemetry.sdk.metrics.export import PeriodicExportingMetricReader
from opentelemetry.exporter.cloud_monitoring import CloudMonitoringMetricsExporter
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor

provider = None

try:
    exporter = CloudMonitoringMetricsExporter(project_id=os.getenv("PROJECT_ID"))
    reader = PeriodicExportingMetricReader(exporter, export_interval_millis=60000)
    provider = MeterProvider(metric_readers=[reader])
    metrics.set_meter_provider(provider)
    print("OpenTelemetry Google Cloud Metrics Exporter initialized.")
except Exception as e:
    print(f"Failed to initialize OpenTelemetry Google Cloud Metrics Exporter: {e}")

# 1. Initialize Firebase Admin and Firestore Client
if not firebase_admin._apps:
    firebase_admin.initialize_app()

from google.cloud import firestore as gcloud_firestore
database_id = os.getenv("FIRESTORE_DATABASE")
if not database_id:
    raise RuntimeError("FIRESTORE_DATABASE environment variable is required but not set.")
db = gcloud_firestore.Client(database=database_id)

# HTTP Bearer Security scheme for Firebase ID Tokens
security = HTTPBearer()

def get_current_user_uid(credentials: HTTPAuthorizationCredentials = Depends(security)) -> str:
    """
    Decrypts and validates the Firebase ID Token (JWT) sent in the Authorization header.
    Returns the user's UID or raises 401 Unauthorized if invalid/expired.
    """
    token = credentials.credentials
    try:
        decoded_token = auth.verify_id_token(token)
        return decoded_token["uid"]
    except Exception as e:
        raise HTTPException(
            status_code=401,
            detail=f"Invalid or expired authentication token: {str(e)}"
        )

# 2. FastAPI Setup
app = FastAPI(title="SRE GenAI Agent Backend")

FastAPIInstrumentor.instrument_app(app)

allowed_origins_env = os.getenv("ALLOWED_ORIGINS", "http://localhost:3000")
allowed_origins = [origin.strip() for origin in allowed_origins_env.split(",") if origin.strip()]
app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True if allowed_origins != ["*"] else False,
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
    products: list = []

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
async def chat(request: ChatRequest, user_uid: str = Depends(get_current_user_uid)):
    session_id = request.session_id or str(uuid.uuid4())
    user_query = request.message

    # Load history
    history = get_session_history(session_id)

    try:
        # Run orchestrator
        agent_res = await run_text_chat(user_query, history, user_uid=user_uid)
        agent_reply = agent_res["text"]
        products = agent_res["products"]
    except GuardrailException as ge:
        # If blocked by the Pre-LLM safety guardrail
        return ChatResponse(text=str(ge), session_id=session_id, products=[])
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Agent execution failed: {str(e)}")

    # Update and save history
    history.append({"role": "user", "content": user_query})
    history.append({"role": "model", "content": agent_reply})
    save_session_history(session_id, history, user_uid)

    return ChatResponse(text=agent_reply, session_id=session_id, products=products)

@app.post("/visual-search")
async def visual_search(
    image: UploadFile = File(...),
    message: str = Form(default=""),
    session_id: str = Form(default=""),
    user_uid: str = Depends(get_current_user_uid)
):
    active_session_id = session_id or str(uuid.uuid4())
    
    try:
        # File size validation (Max 10MB)
        MAX_FILE_SIZE = 10 * 1024 * 1024
        if image.size and image.size > MAX_FILE_SIZE:
            raise HTTPException(status_code=400, detail="Image size exceeds maximum limit of 10MB.")

        # Read uploaded image bytes
        image_bytes = await image.read()
        
        # Run visual search workflow
        search_result = await run_visual_search(image_bytes, message, user_uid=user_uid)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Visual search failed: {str(e)}")

    # Save to session history
    history = get_session_history(active_session_id)
    history.append({"role": "user", "content": f"[Buscou por Imagem] {message}".strip()})
    history.append({"role": "model", "content": search_result["text"]})
    save_session_history(active_session_id, history, user_uid)

    return {
        "text": search_result["text"],
        "products": search_result["products"],
        "session_id": active_session_id
    }

@app.get("/health")
def health():
    return {"status": "healthy"}
