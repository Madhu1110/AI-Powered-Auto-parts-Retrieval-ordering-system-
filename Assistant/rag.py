import json
from pathlib import Path
from sentence_transformers import SentenceTransformer
import faiss
import numpy as np

# Get the path to data directory (relative to this file)
BASE_DIR = Path(__file__).parent.parent
DATA_FILE = BASE_DIR / 'data' / 'products.json'

# Load model (lightweight model for embeddings)
model = SentenceTransformer('all-MiniLM-L6-v2')

# Load product data
try:
    with open(DATA_FILE, 'r', encoding='utf-8') as f:
        products = json.load(f)
except FileNotFoundError:
    raise FileNotFoundError(f"Could not find products.json at {DATA_FILE}")

# Prepare text data for indexing
texts = []
for p in products:
    # Create rich text representation for embeddings
    text = f"{p['name']} {p['category']} {p['brand']} {p['vehicle_fitment']}"
    texts.append(text)

# Create embeddings
print(f"[RAG] Indexing {len(products)} products...")
embeddings = model.encode(texts, show_progress_bar=False)

# Store in FAISS index (L2 distance - more stable for similarity)
dimension = embeddings.shape[1]
index = faiss.IndexFlatL2(dimension)
index.add(np.array(embeddings, dtype=np.float32))

print(f"[RAG] Index created with {len(products)} products")


def retrieve(query, k=3):
    """
    Retrieve top-k relevant products for a query using embeddings.
    
    Args:
        query (str): User's search query
        k (int): Number of results to return (default: 5)
    
    Returns:
        str: Formatted string of relevant products for LLM context
    """
    try:
        # Encode the query
        query_embedding = model.encode([query], show_progress_bar=False)
        
        # Search in FAISS index
        distances, indices = index.search(
            np.array(query_embedding, dtype=np.float32), 
            min(k, len(products))  # Ensure k doesn't exceed dataset size
        )
        
        # Retrieve products
        retrieved_products = [products[i] for i in indices[0] if i < len(products)]
        
        if not retrieved_products:
            return "No products found in catalog."
        
        # Format as context string for LLM
        context = "Available Products:\n"
        context += "-" * 80 + "\n"
        
        for i, p in enumerate(retrieved_products, 1):
            context += f"{i}. {p['name']}\n"
            context += f"   SKU: {p['sku']} | Category: {p['category']}\n"
            context += f"   Brand: {p['brand']} | Vehicle: {p['vehicle_fitment']}\n"
            context += f"   Price: ₹{p['price_inr']} | Stock: {p['stock']} units\n"
            context += f"   Description: {p['description']}\n"
            context += "-" * 80 + "\n"
        
        return context.strip()
    
    except Exception as e:
        print(f"[ERROR] Retrieval failed: {e}")
        return f"Error retrieving products: {str(e)}"