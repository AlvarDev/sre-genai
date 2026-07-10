import os
from google.adk.agents.llm_agent import Agent
from google import genai
from google.genai import types
import vertexai
from vertexai.generative_models import GenerativeModel, Content, Part
from agent.search import search_catalog_tool, search_catalog_by_image_tool
from agent.guardrail import validate_user_input, filter_retrieved_products

# 1. Initialize Vertex AI
project_id = os.getenv("PROJECT_ID")
location = os.getenv("LOCATION", "us-central1")

if not project_id:
    raise RuntimeError("PROJECT_ID environment variable is required but not set.")

if os.getenv("LOCAL_DEVELOPMENT") != "true":
    vertexai.init(project=project_id, location=location)

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

# 3. Instantiate the ADK Agent
# This agent handles standard conversational and text-based searches using Gemini 3.1 Flash.
core_agent = Agent(
    model=os.getenv("CORE_MODEL", "gemini-3.1-flash"),
    name="google_store_assistant",
    description="Virtual assistant for the Google Store catalog.",
    instruction=system_instruction,
    tools=[search_store_catalog]
)

def run_text_chat(user_query: str, chat_history: list) -> str:
    """
    Processes a text query. Validates input, updates history, and returns the response.
    """
    # 1. Pre-LLM Guardrail check
    safe_query = validate_user_input(user_query)
    
    # 2. Format history for ADK agent
    # In a production app, ADK manages session history. 
    # For this service gateway, we can run the agent with the query.
    response = core_agent.run(safe_query)
    return response.text if hasattr(response, "text") else str(response)

def run_visual_search(image_bytes: bytes, user_query: str = "") -> dict:
    """
    Executes the visual search flow:
    1. Generates multimodal image embedding using Gemini Embedding 2.
    2. Queries Firestore via MCP for visually similar products.
    3. Silently filters off-topic drift products (groceries).
    4. Injects clean products into Gemini context to answer the user.
    """
    # 1. Generate Image Embedding Vector
    if os.getenv("LOCAL_DEVELOPMENT") == "true" and not os.getenv("GOOGLE_APPLICATION_CREDENTIALS"):
        # Local development offline simulation: dummy vector (768 dimensions)
        image_embedding = [0.1] * 768
    else:
        # Load Gemini Embedding 2 model using google-genai client routed through Vertex AI 'us' multi-region
        client = genai.Client(vertexai=True, project=project_id, location="us")
        result = client.models.embed_content(
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
    
    if os.getenv("LOCAL_DEVELOPMENT") == "true" and not os.getenv("GOOGLE_APPLICATION_CREDENTIALS"):
        # Mock LLM response for offline testing
        if "No visually matching" in clean_results or "No matching products" in clean_results:
            response_text = "Desculpe, não encontramos nenhum produto correspondente na Google Store."
        else:
            response_text = "Encontrei estes produtos semelhantes na nossa loja! Veja abaixo:"
    else:
        model = GenerativeModel(os.getenv("CORE_MODEL", "gemini-3.1-flash"))
        response = model.generate_content(grounding_prompt)
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
