import base64
import contextvars
import os
import logging
import time
import uuid
from google.adk.agents import Agent
from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from google.adk import Event
from google.adk.models.google_llm import Gemini
from google.adk.models.lite_llm import LiteLlm
from google.genai import types
import vertexai
from vertexai.preview import prompts

from agent.search import call_catalog_text_search, call_catalog_image_search
from agent.guardrail import validate_user_input, filter_retrieved_products

# 1. Initialize Google Cloud project details
project_id = os.getenv("PROJECT_ID")
if not project_id:
    raise RuntimeError("PROJECT_ID environment variable is required but not set.")

gemini_location = os.getenv("GEMINI_LOCATION")
if not gemini_location:
    raise RuntimeError("GEMINI_LOCATION environment variable is required but not set.")

# Initialize Vertex AI for Prompt Management (Prompts are stored regionally)
vertex_prompt_location = os.getenv("VERTEX_PROMPT_LOCATION")
if not vertex_prompt_location:
    raise RuntimeError("VERTEX_PROMPT_LOCATION environment variable is required but not set.")

vertexai.init(project=project_id, location=vertex_prompt_location)
VERTEX_PROMPT_ID = os.getenv("VERTEX_PROMPT_ID")
if not VERTEX_PROMPT_ID:
    raise RuntimeError("VERTEX_PROMPT_ID environment variable is required but not set.")
PROMPT_CACHE_TTL = int(os.getenv("PROMPT_CACHE_TTL_SECONDS", "600"))  # 10 minutes cache

logger = logging.getLogger("orchestrator.prompt_loader")
_cached_instruction: str | None = None
_last_prompt_fetch_time: float = 0.0

def get_system_instruction() -> str:
    """
    Retrieves the system instruction from Vertex AI Prompt Management with an in-memory TTL cache.
    Fails-fast (raises RuntimeError) if Prompt Management is unavailable.
    
    FUTURE ARCHITECTURE NOTE:
    In an upcoming release, when a prompt is published in Vertex AI Prompt Management,
    it will be asynchronously replicated to a Google Cloud Storage bucket (e.g. gs://sre-genai-prompts/system_prompt.txt).
    The secondary fallback will then read from that Cloud Storage mirror if Vertex AI Prompt Management is unreachable.
    """
    global _cached_instruction, _last_prompt_fetch_time
    now = time.time()
    if _cached_instruction and (now - _last_prompt_fetch_time < PROMPT_CACHE_TTL):
        return _cached_instruction

    try:
        logger.info(f"Fetching prompt from Vertex AI Prompt Management (ID: {VERTEX_PROMPT_ID})...")
        managed_prompt = prompts.get(prompt_id=VERTEX_PROMPT_ID)
        instruction = managed_prompt.system_instruction or managed_prompt.prompt_data
        if not instruction:
            raise ValueError(f"Managed prompt '{VERTEX_PROMPT_ID}' contains empty system instruction.")
        _cached_instruction = str(instruction)
        _last_prompt_fetch_time = now
        logger.info("Successfully fetched and cached prompt from Vertex AI Prompt Management.")
        return _cached_instruction
    except Exception as e:
        logger.error(f"Vertex AI Prompt Management failure: {e}", exc_info=True)
        raise RuntimeError(f"Failed to fetch prompt from Vertex AI Prompt Management (ID: {VERTEX_PROMPT_ID}): {e}") from e

# Load initial prompt at module startup (Fail-fast verification)
system_instruction = get_system_instruction()

# Setup the LLM model connection
model_name = os.getenv("CORE_MODEL", "gemini-3.8-flash")
if "gemma" in model_name.lower():
    inference_endpoint = os.getenv("INFERENCE_ENDPOINT")
    if not inference_endpoint:
        raise RuntimeError("INFERENCE_ENDPOINT environment variable is required when using a Gemma model.")
    core_model = LiteLlm(
        model=f"openai/{model_name}",
        api_base=inference_endpoint,
        api_key="local"
    )
else:
    core_model = Gemini(
        model=model_name,
        client_kwargs={
            "vertexai": True,
            "project": project_id,
            "location": gemini_location
        }
    )

# Async-safe ContextVars for passing active image bytes and mime-type to the visual tool
current_image_bytes: contextvars.ContextVar[bytes | None] = contextvars.ContextVar("current_image_bytes", default=None)
current_image_mime: contextvars.ContextVar[str] = contextvars.ContextVar("current_image_mime", default="image/jpeg")

# Static ADK Tools and Agents initialized at module startup
async def search_catalog_by_text(query_text: str) -> str:
    """
    Search the Google Store product catalog using a natural language text query.
    Always use this tool when a customer asks about product pricing, specs, or availability by text,
    or when they request attribute modifications/filters on an image (e.g. asking for another color or category).
    """
    raw_results = await call_catalog_text_search(query_text)
    return await filter_retrieved_products(raw_results)

async def search_catalog_by_image() -> str:
    """
    Search the Google Store product catalog using visual similarity with the customer's uploaded image.
    Use this tool when the customer provides an image and asks if the store carries that item or similar items
    without requesting attribute modifications (e.g. 'Do you have this?', 'Anything similar?', or when no text is provided).
    CRITICAL: Do NOT use this tool if the user requests attribute modifications in text (e.g. asking for a different color, size, or category). In that case, call search_catalog_by_text instead.
    """
    img_bytes = current_image_bytes.get()
    if not img_bytes:
        return "No image was provided in this request."

    image_b64 = base64.b64encode(img_bytes).decode("utf-8")
    raw_results = await call_catalog_image_search(image_b64, mime_type=current_image_mime.get())
    return await filter_retrieved_products(raw_results)

store_assistant_agent = Agent(
    name="store_assistant",
    model=core_model,
    instruction=system_instruction,
    tools=[search_catalog_by_text, search_catalog_by_image]
)

def parse_structured_products(clean_results: str) -> list[dict]:
    """
    Helper to parse raw catalog tool output text into structured dictionaries for the UI.
    Deduplicates products by parent_sku across multiple tool invocations.
    """
    structured_products = []
    seen_skus = set()
    if clean_results and "No matching products" not in clean_results and "No visually matching" not in clean_results:
        parts = clean_results.split("\n---\n")
        for part in parts:
            if not part.strip():
                continue
            lines = part.strip().split("\n")
            p_dict = {}
            for line in lines:
                if line.startswith("Title:"):
                    p_dict["title"] = line.replace("Title:", "").strip()
                elif line.startswith("SKU:"):
                    p_dict["parent_sku"] = line.replace("SKU:", "").strip()
                elif line.startswith("Price:"):
                    p_dict["retail_price"] = line.replace("Price: R$", "").replace("Price:", "").strip()
                elif line.startswith("Description:"):
                    p_dict["shortdesc"] = line.replace("Description:", "").strip()
                elif line.startswith("Image URL:"):
                    p_dict["img_url"] = line.replace("Image URL:", "").strip()
            if p_dict:
                sku = p_dict.get("parent_sku")
                if sku and sku in seen_skus:
                    continue
                if sku:
                    seen_skus.add(sku)
                structured_products.append(p_dict)
    return structured_products

async def execute_text_chat(user_query: str, chat_history: list, user_uid: str = "") -> dict:
    """
    Processes a conversational text query using the ADK Agent. Validates input, updates history, and returns the response.
    """
    # 1. Pre-LLM Guardrail check
    safe_query = await validate_user_input(user_query)

    # 2. Setup in-memory session service and create session
    session_service = InMemorySessionService()
    active_uid = user_uid or "authenticated_user"
    session_id = "session_" + str(uuid.uuid4())[:8]

    session = await session_service.create_session(
        app_name="store_assistant",
        user_id=active_uid,
        session_id=session_id
    )

    # 3. Populate session history from chat_history
    for msg in chat_history:
        role = "user" if msg["role"] == "user" else "model"
        content = types.Content(
            role=role,
            parts=[types.Part.from_text(text=msg["content"])]
        )
        event = Event(
            author="user" if role == "user" else "store_assistant",
            content=content,
            turn_complete=True
        )
        await session_service.append_event(session, event)

    # Ensure agent is using the current cached prompt (refreshes every 10m)
    store_assistant_agent.instruction = get_system_instruction()

    # 4. Initialize ADK Runner
    runner = Runner(
        app_name="store_assistant",
        agent=store_assistant_agent,
        session_service=session_service,
        auto_create_session=True
    )

    # 5. Run the agent and collect response
    new_msg = types.Content(role="user", parts=[types.Part.from_text(text=safe_query)])
    response_text = ""
    retrieved_catalog_text = ""
    async for event in runner.run_async(user_id=active_uid, session_id=session_id, new_message=new_msg):
        if event.content and event.content.parts:
            for part in event.content.parts:
                if part.text:
                    response_text += part.text
                if hasattr(part, "function_response") and part.function_response:
                    resp = part.function_response.response
                    if isinstance(resp, dict):
                        retrieved_catalog_text += "\n".join(str(val) for val in resp.values())
                    elif isinstance(resp, str):
                        retrieved_catalog_text += resp

    structured_products = parse_structured_products(retrieved_catalog_text)

    return {
        "text": response_text,
        "products": structured_products
    }

async def execute_visual_chat(
    image_bytes: bytes,
    user_query: str = "",
    chat_history: list = None,
    user_uid: str = "",
    mime_type: str = "image/jpeg"
) -> dict:
    """
    Executes multimodal conversational chat using the ADK Agent. Validates text guardrail,
    passes image + text parts to the agent, and lets the LLM autonomously choose the search tool.
    """
    # 1. Pre-LLM Guardrail check on optional user query
    safe_query = await validate_user_input(user_query) if user_query and user_query.strip() else ""

    # 2. Set context variables for tool access
    token = current_image_bytes.set(image_bytes)
    mime_token = current_image_mime.set(mime_type)

    session_service = InMemorySessionService()
    active_uid = user_uid or "authenticated_user"
    session_id = "visual_" + str(uuid.uuid4())[:8]

    try:
        session = await session_service.create_session(
            app_name="store_assistant",
            user_id=active_uid,
            session_id=session_id
        )

        # Populate previous conversation history if available
        if chat_history:
            for msg in chat_history:
                role = "user" if msg["role"] == "user" else "model"
                content = types.Content(
                    role=role,
                    parts=[types.Part.from_text(text=msg["content"])]
                )
                event = Event(
                    author="user" if role == "user" else "store_assistant",
                    content=content,
                    turn_complete=True
                )
                await session_service.append_event(session, event)

        # Ensure agent is using the current cached prompt (refreshes every 10m)
        store_assistant_agent.instruction = get_system_instruction()

        runner = Runner(
            app_name="store_assistant",
            agent=store_assistant_agent,
            session_service=session_service,
            auto_create_session=True
        )

        # Multimodal payload: image bytes + safe user query
        parts = [types.Part.from_bytes(data=image_bytes, mime_type=mime_type)]
        if safe_query:
            parts.append(types.Part.from_text(text=safe_query))
        else:
            parts.append(types.Part.from_text(text="O usuário enviou esta imagem buscando produtos no catálogo da Google Store."))

        new_msg = types.Content(role="user", parts=parts)
        response_text = ""
        retrieved_catalog_text = ""

        async for event in runner.run_async(user_id=active_uid, session_id=session_id, new_message=new_msg):
            if event.content and event.content.parts:
                for part in event.content.parts:
                    if part.text:
                        response_text += part.text
                    if hasattr(part, "function_response") and part.function_response:
                        resp = part.function_response.response
                        if isinstance(resp, dict):
                            retrieved_catalog_text += "\n".join(str(val) for val in resp.values())
                        elif isinstance(resp, str):
                            retrieved_catalog_text += resp

        structured_products = parse_structured_products(retrieved_catalog_text)

        return {
            "text": response_text,
            "products": structured_products
        }
    finally:
        current_image_bytes.reset(token)
        current_image_mime.reset(mime_token)
