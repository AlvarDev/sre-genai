import uuid
from fastapi import FastAPI, Depends, HTTPException, UploadFile, File, Form
from auth import get_current_user_uid
from models import ChatRequest, ChatResponse
from database import get_session_history, save_session_history
from agent.orchestrator import run_text_chat, run_visual_search
from agent.guardrail import GuardrailException

def register_chat_routes(app: FastAPI):
    @app.post("/chat", response_model=ChatResponse)
    async def chat(request: ChatRequest, user_uid: str = Depends(get_current_user_uid)):
        session_id = request.session_id or str(uuid.uuid4())
        user_query = request.message

        history = get_session_history(session_id, user_uid)

        try:
            agent_res = await run_text_chat(user_query, history, user_uid=user_uid)
            agent_reply = agent_res["text"]
            products = agent_res["products"]
        except GuardrailException as ge:
            return ChatResponse(text=str(ge), session_id=session_id, products=[])
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Agent execution failed: {str(e)}")

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
            MAX_FILE_SIZE = 10 * 1024 * 1024
            if image.size and image.size > MAX_FILE_SIZE:
                raise HTTPException(status_code=400, detail="Image size exceeds maximum limit of 10MB.")

            image_bytes = await image.read()
            search_result = await run_visual_search(image_bytes, message, user_uid=user_uid)
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Visual search failed: {str(e)}")

        history = get_session_history(active_session_id, user_uid)
        history.append({"role": "user", "content": f"[Buscou por Imagem] {message}".strip()})
        history.append({"role": "model", "content": search_result["text"]})
        save_session_history(active_session_id, history, user_uid)

        return {
            "text": search_result["text"],
            "products": search_result["products"],
            "session_id": active_session_id
        }
