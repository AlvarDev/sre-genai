import os
import uuid
from google.adk.agents import Agent
from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from google.adk import Event
from google.adk.models.google_llm import Gemini
from google.genai import types

from agent.search import search_catalog_tool, search_catalog_by_image_tool
from agent.guardrail import validate_user_input, filter_retrieved_products

# 1. Initialize Google Cloud project details
project_id = os.getenv("PROJECT_ID")
location = os.getenv("LOCATION", "us")

if not project_id:
    raise RuntimeError("PROJECT_ID environment variable is required but not set.")

# Load System Prompt
prompt_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "system_prompt.txt")
with open(prompt_path, "r", encoding="utf-8") as f:
    system_instruction = f.read()

# Setup the Gemini model connection
model_name = os.getenv("CORE_MODEL", "gemini-3.1-flash-lite")
gemini_model = Gemini(
    model=model_name,
    client_kwargs={
        "vertexai": True,
        "project": project_id,
        "location": location
    }
)

async def run_text_chat(user_query: str, chat_history: list) -> dict:
    """
    Processes a text query using ADK LlmAgent. Validates input, updates history, and returns the response.
    """
    # 1. Pre-LLM Guardrail check
    safe_query = validate_user_input(user_query)
    
    structured_products = []

    # 2. Define the RAG Tool exposed to the LLM
    def search_store_catalog(query_text: str) -> str:
        """
        Search the Google Store product catalog for tech devices and apparel matching the query.
        Always use this tool when a customer asks about product pricing, specs, or availability.
        """
        # 1. Query the Catalog MCP Server
        raw_results = search_catalog_tool(query_text)
        
        # 2. Filter results through the Post-RAG Guardrail
        clean_results = filter_retrieved_products(raw_results)
        
        # Parse clean_results into structured_products for the UI
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
                    structured_products.append(p_dict)
                    
        return clean_results

    # 3. Define the ADK Agent
    store_assistant_agent = Agent(
        name="store_assistant",
        model=gemini_model,
        instruction=system_instruction,
        tools=[search_store_catalog]
    )

    # 4. Setup in-memory session service and create session
    session_service = InMemorySessionService()
    user_uid = "anonymous"
    session_id = "session_" + str(uuid.uuid4())[:8]

    session = await session_service.create_session(
        app_name="store_assistant",
        user_id=user_uid,
        session_id=session_id
    )

    # 5. Populate session history from chat_history
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

    # 6. Initialize ADK Runner
    runner = Runner(
        app_name="store_assistant",
        agent=store_assistant_agent,
        session_service=session_service,
        auto_create_session=True
    )

    # 7. Run the agent and collect response
    new_msg = types.Content(role="user", parts=[types.Part.from_text(text=safe_query)])
    response_text = ""
    async for event in runner.run_async(user_id=user_uid, session_id=session_id, new_message=new_msg):
        if event.content and event.content.parts:
            for part in event.content.parts:
                if part.text:
                    response_text += part.text

    return {
        "text": response_text,
        "products": structured_products
    }

async def run_visual_search(image_bytes: bytes, user_query: str = "") -> dict:
    """
    Executes the visual search flow using ADK Agent.
    """
    # 1. Generate Image Embedding Vector (using raw Client since this is embedding generation, not agent conversation)
    from google.genai import Client
    us_client = Client(vertexai=True, project=project_id, location="us")
    result = us_client.models.embed_content(
        model="gemini-embedding-2",
        contents=[
            types.Part.from_bytes(
                data=image_bytes,
                mime_type="image/jpeg"
            )
        ],
        config=types.EmbedContentConfig(output_dimensionality=768)
    )
    image_embedding = result.embeddings[0].values

    # 2. Search catalog by image vector
    raw_results = search_catalog_by_image_tool(image_embedding)
    
    # 3. Post-RAG Guardrail filter (silently strips off-topic items)
    clean_results = filter_retrieved_products(raw_results)
    
    # 4. Generate conversational response grounded in the clean products
    grounding_prompt = (
        f"{system_instruction}\n\n"
        "Você recebeu uma busca por imagem.\n"
        f"Resultados da busca no banco de dados (PRODUTOS): \n{clean_results}\n\n"
        f"Comentário opcional do usuário: {user_query or 'Nenhum'}\n\n"
        "Com base nos PRODUTOS fornecidos acima, responda ao usuário em português brasileiro sobre o que você encontrou."
    )
    
    # Define Grounding Agent via ADK
    grounding_agent = Agent(
        name="grounding_agent",
        model=gemini_model,
        instruction=system_instruction
    )

    session_service = InMemorySessionService()
    user_uid = "anonymous"
    session_id = "visual_" + str(uuid.uuid4())[:8]

    runner = Runner(
        app_name="visual_search",
        agent=grounding_agent,
        session_service=session_service,
        auto_create_session=True
    )

    new_msg = types.Content(role="user", parts=[types.Part.from_text(text=grounding_prompt)])
    response_text = ""
    async for event in runner.run_async(user_id=user_uid, session_id=session_id, new_message=new_msg):
        if event.content and event.content.parts:
            for part in event.content.parts:
                if part.text:
                    response_text += part.text

    # 5. Extract individual products for structured UI rendering
    structured_products = []
    if "No matching products" not in clean_results and "No visually matching" not in clean_results:
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
                structured_products.append(p_dict)
                
    return {
        "text": response_text,
        "products": structured_products
    }
