import os
from google.cloud import firestore
from google.cloud.firestore_v1.vector import Vector

# 1. Initialize Firestore Client
project_id = os.getenv("PROJECT_ID")
database_id = os.getenv("FIRESTORE_DATABASE")
if not project_id or not database_id:
    raise RuntimeError("PROJECT_ID and FIRESTORE_DATABASE environment variables are required.")
db = firestore.Client(project=project_id, database=database_id)

# 2. Define the off-topic grocery items to inject/remove
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
    
    collection = db.collection("products")

    for i, p in enumerate(grocery_items):
        print(f"Injecting drift item {i+1}/2: {p['title']}...")
        
        # Combine text fields to generate embedding input
        combined_text = f"{p['title']} {p['shortdesc']} {p['longdesc']} {p['keywords']}"
        
        # Generate real semantic vector embedding using gemini-embedding-2
        try:
            from google.genai import Client, types
            client = Client(vertexai=True, project=project_id, location="us")
            res = client.models.embed_content(
                model="gemini-embedding-2",
                contents=combined_text,
                config=types.EmbedContentConfig(output_dimensionality=768)
            )
            image_vector = res.embeddings[0].values
            print(f"Generated real embedding vector for: {p['title']}")
        except Exception as embed_err:
            print(f"Failed to generate real embedding vector: {embed_err}")
            image_vector = [0.9] * 768
        
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
            "image_embeddings": Vector(image_vector)
        }
        
        # Write to Firestore
        collection.document(p["parent_sku"]).set(doc_data)
        print(f"drift item successfully injected: {p['parent_sku']}")

    print("Database drift contamination complete.")

def remove_database_drift():
    print("Removing off-topic database drift (grocery items) from 'sre-genai' database...")
    collection = db.collection("products")
    
    for p in grocery_items:
        sku = p["parent_sku"]
        doc_ref = collection.document(sku)
        
        # Check if document exists before deleting
        if doc_ref.get().exists:
            doc_ref.delete()
            print(f"drift item successfully removed: {sku}")
        else:
            print(f"drift item not found, skipping: {sku}")
            
    print("Database cleanup complete.")

if __name__ == "__main__":
    print("Select an option:")
    print("1. Inject grocery drift (contaminate database)")
    print("2. Remove grocery drift (clean database)")
    choice = input("Enter option (1 or 2): ").strip()
    
    if choice == "1":
        confirm = input("Are you sure you want to contaminate the database with grocery drift? (y/N): ")
        if confirm.lower() == 'y':
            inject_database_drift()
        else:
            print("Injection aborted.")
    elif choice == "2":
        confirm = input("Are you sure you want to remove the grocery drift? (y/N): ")
        if confirm.lower() == 'y':
            remove_database_drift()
        else:
            print("Cleanup aborted.")
    else:
        print("Invalid option selected.")
