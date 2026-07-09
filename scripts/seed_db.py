import os
import csv
import json
from google.cloud import firestore
from google.cloud.firestore_v1.vector import Vector

# 1. Initialize Firestore Client
db = firestore.Client(database="sre-genai")

def generate_embeddings_and_seed():
    print("Starting database seed for database: sre-genai using CSV file")
    
    csv_file_path = os.path.join(os.path.dirname(__file__), "image_data_with_embeddings.csv")
    if not os.path.exists(csv_file_path):
        print(f"Error: CSV file not found at {csv_file_path}")
        return

    collection = db.collection("products")
    
    with open(csv_file_path, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        rows = list(reader)
        
    print(f"Loaded {len(rows)} products from CSV.")

    # Firestore batching is recommended for large writes (max 500 operations per batch)
    batch = db.batch()
    batch_count = 0
    total_written = 0

    for i, row in enumerate(rows):
        parent_sku = row["parent_sku"]
        title = row["title"]
        retail_price = float(row["retail_price"]) if row["retail_price"] else 0.0
        
        # Parse pre-computed image embedding vector
        try:
            image_vector = json.loads(row["image_embeddings"])
        except Exception as e:
            print(f"Warning: Failed to parse image embedding for {parent_sku}: {e}")
            continue

        doc_data = {
            "parent_sku": parent_sku,
            "parent_description": row.get("parent_description", ""),
            "title": title,
            "retail_price": retail_price,
            "img_url": row["img_url"],
            "seo_url": row["seo_url"],
            "shortdesc": row["shortdesc"],
            "longdesc": row["longdesc"],
            "keywords": row["keywords"],
            "metadescription": row.get("metadescription", ""),
            "file_path": row.get("file_path", ""),
            "gcs_path": row.get("gcs_path", ""),
            "combined_text": row["combined_text"],
            "image_embeddings": Vector(image_vector)
        }

        doc_ref = collection.document(parent_sku)
        batch.set(doc_ref, doc_data)
        batch_count += 1
        
        if batch_count >= 500:
            batch.commit()
            total_written += batch_count
            print(f"Committed batch of {batch_count} records. Total written: {total_written}")
            batch = db.batch()
            batch_count = 0

    if batch_count > 0:
        batch.commit()
        total_written += batch_count
        print(f"Committed final batch of {batch_count} records. Total written: {total_written}")

    print("Database seeding completed successfully.")

if __name__ == "__main__":
    generate_embeddings_and_seed()
