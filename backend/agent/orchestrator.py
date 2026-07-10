import os
from google import genai
from google.genai import types
from agent.search import search_catalog_tool, search_catalog_by_image_tool
from agent.guardrail import validate_user_input, filter_retrieved_products

# 1. Initialize Google Cloud project details
project_id = os.getenv("PROJECT_ID")
location = os.getenv("LOCATION", "us")

if not project_id:
    raise RuntimeError("PROJECT_ID environment variable is required but not set.")

# Initialize the new Google GenAI Client globally for chat generation
client = genai.Client(vertexai=True, project=project_id, location=location)

# Load System Prompt
prompt_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "system_prompt.txt")
with open(prompt_path, "r", encoding="utf-8") as f:
    system_instruction = f.read()

# 2. Define the RAG Tool exposed to the LLM
def search_store_catalog(query_text: str) -> str:
    """
    Search the Google Store product catalog for tech devices and apparel matching the query.
    Always use this tool when a customer asks about product pricing, specs, or availability.
    """
    # 1. Query the Catalog MCP Server
    raw_results = search_catalog_tool(query_text)
    
    # 2. Filter results through the Post-RAG Guardrail Agent
    clean_results = filter_retrieved_products(raw_results)
    
    return clean_results

def run_text_chat(user_query: str, chat_history: list) -> dict:
    """
    Processes a text query. Validates input, updates history, and returns the response.
    """
    # 1. Pre-LLM Guardrail check
    safe_query = validate_user_input(user_query)
    
    # 2. Convert incoming history to Google GenAI Content format
    formatted_history = []
    for msg in chat_history:
        role = "user" if msg["role"] == "user" else "model"
        formatted_history.append(
            types.Content(
                role=role,
                parts=[types.Part.from_text(text=msg["content"])]
            )
        )
    
    # 3. Create a chat session with automatic function calling enabled
    chat = client.chats.create(
        model=os.getenv("CORE_MODEL", "gemini-3.1-flash-lite"),
        config=types.GenerateContentConfig(
            system_instruction=system_instruction,
            tools=[search_store_catalog]
        ),
        history=formatted_history
    )
    
    # 4. Execute chat request
    response = chat.send_message(safe_query)
    
    # 5. Extract products from function responses in the chat history
    structured_products = []
    try:
        for content in chat.get_history():
            if not content.parts:
                continue
            for part in content.parts:
                if part.function_response:
                    resp_val = part.function_response.response
                    if isinstance(resp_val, dict):
                        result_str = resp_val.get("result") or resp_val.get("output") or ""
                        if not result_str and resp_val:
                            result_str = next(iter(resp_val.values()))
                        
                        if isinstance(result_str, str) and result_str:
                            parts = result_str.split("\n---\n")
                            for p_part in parts:
                                if not p_part.strip():
                                    continue
                                lines = p_part.strip().split("\n")
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
    except Exception as e:
        print(f"Error parsing products from chat history: {e}")
        
    return {
        "text": response.text,
        "products": structured_products
    }

def run_visual_search(image_bytes: bytes, user_query: str = "") -> dict:
    """
    Executes the visual search flow:
    1. Generates multimodal image embedding using Gemini Embedding 2.
    2. Queries Firestore via MCP for visually similar products.
    3. Silently filters off-topic drift products (groceries).
    4. Injects clean products into Gemini context to answer the user.
    """
    # 1. Generate Image Embedding Vector
    # Load Gemini Embedding 2 model using google-genai client routed through Vertex AI 'us' multi-region
    us_client = genai.Client(vertexai=True, project=project_id, location="us")
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
    # We formulate a direct grounding prompt for Gemini
    grounding_prompt = (
        f"{system_instruction}\n\n"
        "Você recebeu uma busca por imagem.\n"
        f"Resultados da busca no banco de dados (PRODUTOS): \n{clean_results}\n\n"
        f"Comentário opcional do usuário: {user_query or 'Nenhum'}\n\n"
        "Com base nos PRODUTOS fornecidos acima, responda ao usuário em português brasileiro sobre o que você encontrou."
    )
    
    response = client.models.generate_content(
        model=os.getenv("CORE_MODEL", "gemini-3.1-flash-lite"),
        contents=grounding_prompt
    )
    response_text = response.text

    # 5. Extract individual products for structured UI rendering
    # We split clean_results back into a list of dictionaries for the frontend carousel
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
