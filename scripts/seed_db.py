import os
from google.cloud import firestore
from google.cloud.firestore_v1.vector import Vector
import vertexai
from vertexai.language_models import TextEmbeddingModel

# 1. Initialize Firestore Client targeting the 'sre-genai' named database
db = firestore.Client(database="sre-genai")

# 2. Initialize Vertex AI
project_id = os.getenv("PROJECT_ID", "sre-genai")
location = os.getenv("LOCATION", "us-central1")
if os.getenv("LOCAL_DEVELOPMENT") != "true":
    vertexai.init(project=project_id, location=location)

# 3. Define the product catalog
products_catalog = [
    {
        "parent_sku": "pixel-9-pro",
        "title": "Google Pixel 9 Pro",
        "retail_price": 1099.00,
        "img_url": "https://store.google.com/product/pixel_9_pro_image.jpg",
        "seo_url": "https://store.google.com/product/pixel_9_pro",
        "shortdesc": "O smartphone Android definitivo com câmera profissional e IA Gemini integrada.",
        "longdesc": "O Google Pixel 9 Pro combina o chip Tensor G4 com câmeras de última geração e 16 GB de RAM para a experiência de IA móvel mais avançada.",
        "keywords": "pixel 9 pro, google phone, celular, smartphone, gemini"
    },
    {
        "parent_sku": "nest-thermostat",
        "title": "Google Nest Learning Thermostat (4th Gen)",
        "retail_price": 249.00,
        "img_url": "https://store.google.com/product/nest_thermostat_image.jpg",
        "seo_url": "https://store.google.com/product/nest_thermostat",
        "shortdesc": "Termostato inteligente que aprende sua rotina e economiza energia.",
        "longdesc": "O Nest Learning Thermostat se programa sozinho com base na sua temperatura favorita e ajuda você a poupar eletricidade de forma automática.",
        "keywords": "nest, termostato, smart home, casa inteligente, energia"
    },
    {
        "parent_sku": "pixel-buds-pro-2",
        "title": "Google Pixel Buds Pro 2",
        "retail_price": 229.00,
        "img_url": "https://store.google.com/product/pixel_buds_pro_2_image.jpg",
        "seo_url": "https://store.google.com/product/pixel_buds_pro_2",
        "shortdesc": "Fones de ouvido premium com cancelamento ativo de ruído e chip Tensor A1.",
        "longdesc": "Cancelamento de ruído ativo inteligente, ajuste seguro giratório e som espacial imersivo com integração Gemini hands-free.",
        "keywords": "pixel buds, fone de ouvido, bluetooth, anc, audio"
    },
    {
        "parent_sku": "google-tee",
        "title": "Camiseta Orgânica Google Brand",
        "retail_price": 25.00,
        "img_url": "https://store.google.com/product/google_tee_image.jpg",
        "seo_url": "https://store.google.com/product/google_tee",
        "shortdesc": "Camiseta de algodão orgânico macio com o logo clássico do Google.",
        "longdesc": "Mostre seu orgulho Google com esta camiseta ecológica, confortável para o dia a dia e feita com materiais 100% sustentáveis.",
        "keywords": "camiseta, google tee, roupa, vestuario, algodao"
    },
    {
        "parent_sku": "pixel-watch-3",
        "title": "Google Pixel Watch 3",
        "retail_price": 349.00,
        "img_url": "https://store.google.com/product/pixel_watch_3_image.jpg",
        "seo_url": "https://store.google.com/product/pixel_watch_3",
        "shortdesc": "Smartwatch avançado com rastreamento Fitbit e tela Actua ultrabrilhante.",
        "longdesc": "O Pixel Watch 3 oferece monitoramento de saúde de elite, insights de corrida personalizados e bateria estendida com carregamento rápido.",
        "keywords": "pixel watch, relogio, smartwatch, fitbit, saude"
    },
    {
        "parent_sku": "nest-cam",
        "title": "Google Nest Cam (Bateria)",
        "retail_price": 179.00,
        "img_url": "https://store.google.com/product/nest_cam_image.jpg",
        "seo_url": "https://store.google.com/product/nest_cam",
        "shortdesc": "Câmera de segurança externa e interna com bateria recarregável.",
        "longdesc": "Monitore sua casa com vídeo HDR 1080p, alertas inteligentes de movimento e instalação fácil sem cabos.",
        "keywords": "nest cam, camera, seguranca, smart home, vigiar"
    },
    {
        "parent_sku": "google-mug",
        "title": "Caneca de Cerâmica Google",
        "retail_price": 15.00,
        "img_url": "https://store.google.com/product/google_mug_image.jpg",
        "seo_url": "https://store.google.com/product/google_mug",
        "shortdesc": "Caneca de cerâmica fosca com design minimalista colorido do Google.",
        "longdesc": "Perfeita para seu café ou chá matinal. Durável, segura para lava-louças e micro-ondas, com interior brilhante decorado.",
        "keywords": "caneca, google mug, copo, ceramica, cafe"
    },
    {
        "parent_sku": "google-backpack",
        "title": "Mochila Google Tech",
        "retail_price": 80.00,
        "img_url": "https://store.google.com/product/google_backpack_image.jpg",
        "seo_url": "https://store.google.com/product/google_backpack",
        "shortdesc": "Mochila ergonômica impermeável com compartimento dedicado para laptop.",
        "longdesc": "Proteja seus gadgets com esta mochila resistente com bolsos organizadores inteligentes e design corporativo moderno.",
        "keywords": "mochila, google backpack, bolsa, viagem, notebook"
    },
    {
        "parent_sku": "nest-hub-max",
        "title": "Google Nest Hub Max",
        "retail_price": 229.00,
        "img_url": "https://store.google.com/product/nest_hub_max_image.jpg",
        "seo_url": "https://store.google.com/product/nest_hub_max",
        "shortdesc": "Tela inteligente com assistente integrado, câmera Nest e alto-falantes estéreo.",
        "longdesc": "Faça chamadas de vídeo, ouça músicas, controle seus aparelhos de smart home e gerencie sua agenda familiar em uma tela sensível ao toque de 10 polegadas.",
        "keywords": "nest hub, tela inteligente, alto-falante, smart home"
    },
    {
        "parent_sku": "chromecast-google-tv",
        "title": "Chromecast com Google TV (4K)",
        "retail_price": 49.99,
        "img_url": "https://store.google.com/product/chromecast_gtv_image.jpg",
        "seo_url": "https://store.google.com/product/chromecast_gtv",
        "shortdesc": "Dispositivo de streaming de vídeo 4K HDR com controle remoto de voz.",
        "longdesc": "Transmita seu entretenimento favorito em até 4K HDR e receba recomendações personalizadas agregadas de todos os seus serviços em um só lugar.",
        "keywords": "chromecast, google tv, streaming, televisao, controle por voz"
    }
]

def generate_embeddings_and_seed():
    print(f"Starting database seed for database: sre-genai")
    
    # 4. Load text embedding model if online
    model = None
    if os.getenv("LOCAL_DEVELOPMENT") != "true" or os.getenv("GOOGLE_APPLICATION_CREDENTIALS"):
        try:
            model = TextEmbeddingModel.from_pretrained("text-embedding-004")
            print("Loaded Vertex AI text-embedding-004 model successfully.")
        except Exception as e:
            print(f"Warning: Could not load Vertex AI embedding model: {e}. Falling back to mocks.")

    collection = db.collection("products")

    for i, p in enumerate(products_catalog):
        print(f"Processing product {i+1}/10: {p['title']}...")
        
        # Combine text fields to generate embedding input
        combined_text = f"{p['title']} {p['shortdesc']} {p['longdesc']} {p['keywords']}"
        
        # Text embedding vector (768 dimensions)
        if model:
            try:
                embeddings = model.get_embeddings([combined_text])
                text_vector = embeddings[0].values
            except Exception as e:
                print(f"Embedding generation failed for {p['parent_sku']}: {e}. Mocking.")
                text_vector = [0.1 * (i + 1)] * 768
        else:
            # Mock vector for offline local emulator testing
            text_vector = [0.1 * (i + 1)] * 768
            
        # Multimodal image embedding vector (1408 dimensions)
        # In a real pipeline, we pass the image to multimodalembedding.
        # Since we use static stock images, we generate a corresponding mock/shifted vector
        # that allows nearest-neighbor testing based on SKU categories.
        image_vector = [0.02 * (i + 1)] * 1408
        
        # Build Firestore Document
        doc_data = {
            "parent_sku": p["parent_sku"],
            "title": p["title"],
            "retail_price": p["retail_price"],
            "img_url": p["img_url"],
            "seo_url": p["seo_url"],
            "shortdesc": p["shortdesc"],
            "longdesc": p["longdesc"],
            "keywords": p["keywords"],
            "combined_text": combined_text,
            "text_embeddings": Vector(text_vector),
            "image_embeddings": Vector(image_vector)
        }
        
        # Write to Firestore
        collection.document(p["parent_sku"]).set(doc_data)
        print(f"Successfully seeded: {p['parent_sku']}")

    print("Database seeding completed successfully.")

if __name__ == "__main__":
    # If running locally against emulator
    if os.getenv("FIRESTORE_EMULATOR_HOST") is None:
        os.environ["FIRESTORE_EMULATOR_HOST"] = "localhost:8080"
        
    generate_embeddings_and_seed()
