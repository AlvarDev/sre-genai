import os
from google.cloud import firestore
from google.cloud.firestore_v1.vector import Vector
import vertexai
from vertexai.language_models import TextEmbeddingModel

# 1. Initialize Firestore Client targeting 'sre-genai' named database
db = firestore.Client(database="sre-genai")

# 2. Initialize Vertex AI
project_id = os.getenv("PROJECT_ID", "sre-genai")
location = os.getenv("LOCATION", "us-central1")
if os.getenv("LOCAL_DEVELOPMENT") != "true":
    vertexai.init(project=project_id, location=location)

# 3. Define the off-topic grocery items to inject
grocery_items = [
    {
        "parent_sku": "organic-potatoes",
        "title": "Batatas Orgânicas Russet (Saco de 2kg)",
        "retail_price": 5.99,
        "img_url": "https://images.unsplash.com/photo-1518977676601-b53f82aba655?w=500",
        "seo_url": "https://store.google.com/product/organic_russet_potatoes",
        "shortdesc": "Batatas Russet orgânicas frescas da fazenda, perfeitas para assar ou fritar.",
        "longdesc": "Nossas batatas orgânicas são cultivadas sem pesticidas químicos. Ricas em amido e extremamente macias quando cozidas.",
        "keywords": "batata, batatas, potato, potatoes, russet, legumes, vegetais, comida, mercado"
    },
    {
        "parent_sku": "fresh-bananas",
        "title": "Banana Nanica Orgânica (Penca com 6 unidades)",
        "retail_price": 3.49,
        "img_url": "https://images.unsplash.com/photo-1571771894821-ce9b6c11b08e?w=500",
        "seo_url": "https://store.google.com/product/organic_bananas",
        "shortdesc": "Bananas maduras orgânicas, ricas em potássio e energia.",
        "longdesc": "Bananas orgânicas certificadas, colhidas no ponto ideal para consumo rápido. Uma opção nutritiva para o café da manhã ou lanches.",
        "keywords": "banana, bananas, fruta, frutas, mercado, comida, potassio"
    }
]

def inject_database_drift():
    print("WARNING: Injecting off-topic database drift (grocery items) into 'sre-genai' database!")
    
    # 4. Load text embedding model if online
    model = None
    if os.getenv("LOCAL_DEVELOPMENT") != "true" or os.getenv("GOOGLE_APPLICATION_CREDENTIALS"):
        try:
            model = TextEmbeddingModel.from_pretrained("text-embedding-004")
            print("Loaded Vertex AI text-embedding-004 model successfully.")
        except Exception as e:
            print(f"Warning: Could not load Vertex AI embedding model: {e}. Mocking.")

    collection = db.collection("products")

    for i, p in enumerate(grocery_items):
        print(f"Injecting drift item {i+1}/2: {p['title']}...")
        
        # Combine text fields to generate embedding input
        combined_text = f"{p['title']} {p['shortdesc']} {p['longdesc']} {p['keywords']}"
        
        # Text embedding vector (768 dimensions)
        if model:
            try:
                embeddings = model.get_embeddings([combined_text])
                text_vector = embeddings[0].values
            except Exception as e:
                print(f"Embedding generation failed for {p['parent_sku']}: {e}. Mocking.")
                text_vector = [0.85] * 768 # High offset to simulate distinct topic
        else:
            # Mock vector for offline local emulator testing
            text_vector = [0.85] * 768
            
        # Multimodal image embedding vector (1408 dimensions)
        # We set an image vector that will trigger matches for "potato" in visual queries
        image_vector = [0.9] * 1408
        
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
        print(f"drift item successfully injected: {p['parent_sku']}")

    print("Database drift contamination complete.")

if __name__ == "__main__":
    if os.getenv("FIRESTORE_EMULATOR_HOST") is None:
        os.environ["FIRESTORE_EMULATOR_HOST"] = "localhost:8080"
        
    inject_drift_choice = input("Are you sure you want to contaminate the production database with grocery drift? (y/N): ")
    if inject_drift_choice.lower() == 'y':
        inject_database_drift()
    else:
        print("Injection aborted.")
