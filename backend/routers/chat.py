import asyncio
import logging
import uuid
from fastapi import FastAPI, Depends, HTTPException, UploadFile, File, Form
from opentelemetry import trace
from auth import get_current_user_uid
from models import ChatRequest, ChatResponse
from database import get_session_history, save_session_history
from agent.orchestrator import execute_text_chat, execute_visual_chat
from agent.guardrail import GuardrailException
from validation import MAX_IMAGE_BYTES, MAX_MESSAGE_CHARS, detect_image_type, read_capped

logger = logging.getLogger("chat")

# Never return exception text to clients; details go to the server log only.
GENERIC_ERROR_DETAIL = "Erro interno ao processar sua solicitação."

def register_chat_routes(app: FastAPI):
    @app.post("/chat", response_model=ChatResponse)
    async def chat(request: ChatRequest, user_uid: str = Depends(get_current_user_uid)):
        session_id = request.session_id or str(uuid.uuid4())
        user_query = request.message

        span = trace.get_current_span()
        if span and span.is_recording():
            span.set_attribute("gen_ai.conversation.id", session_id)
            span.set_attribute("session_id", session_id)
            span.set_attribute("enduser.id", user_uid)

        # database.py uses the synchronous Firestore client; run it off the event loop.
        history = await asyncio.to_thread(get_session_history, session_id, user_uid)

        try:
            agent_res = await execute_text_chat(user_query, history, user_uid=user_uid)
            agent_reply = agent_res["text"]
            products = agent_res["products"]
        except GuardrailException as ge:
            return ChatResponse(text=str(ge), session_id=session_id, products=[])
        except HTTPException:
            raise
        except Exception:
            logger.exception("chat failed")
            raise HTTPException(status_code=500, detail=GENERIC_ERROR_DETAIL)

        history.append({"role": "user", "content": user_query})
        history.append({"role": "model", "content": agent_reply})
        await asyncio.to_thread(save_session_history, session_id, history, user_uid)

        return ChatResponse(text=agent_reply, session_id=session_id, products=products)

    @app.post("/visual-search")
    async def visual_search(
        image: UploadFile = File(...),
        message: str = Form(default=""),
        session_id: str = Form(default=""),
        user_uid: str = Depends(get_current_user_uid)
    ):
        active_session_id = session_id or str(uuid.uuid4())

        span = trace.get_current_span()
        if span and span.is_recording():
            span.set_attribute("gen_ai.conversation.id", active_session_id)
            span.set_attribute("session_id", active_session_id)
            span.set_attribute("enduser.id", user_uid)

        # Validate input before any model or database call.
        if len(message) > MAX_MESSAGE_CHARS:
            raise HTTPException(status_code=422, detail=f"Mensagem muito longa (máx. {MAX_MESSAGE_CHARS} caracteres).")
        try:
            image_bytes = await read_capped(image, MAX_IMAGE_BYTES)
        except ValueError:
            raise HTTPException(status_code=413, detail="Imagem muito grande (máx. 10 MB).")
        detected_mime_type = detect_image_type(image_bytes)
        if detected_mime_type is None:
            raise HTTPException(status_code=415, detail="Formato de imagem não suportado (use JPEG, PNG ou WebP).")

        history = await asyncio.to_thread(get_session_history, active_session_id, user_uid)

        try:
            search_result = await execute_visual_chat(
                image_bytes=image_bytes,
                user_query=message,
                chat_history=history,
                user_uid=user_uid,
                mime_type=detected_mime_type
            )
        except GuardrailException as ge:
            return {
                "text": str(ge),
                "products": [],
                "session_id": active_session_id
            }
        except HTTPException:
            raise
        except Exception:
            logger.exception("visual search failed")
            raise HTTPException(status_code=500, detail=GENERIC_ERROR_DETAIL)

        history.append({"role": "user", "content": f"[Buscou por Imagem] {message}".strip()})
        history.append({"role": "model", "content": search_result["text"]})
        await asyncio.to_thread(save_session_history, active_session_id, history, user_uid)

        return {
            "text": search_result["text"],
            "products": search_result["products"],
            "session_id": active_session_id
        }
