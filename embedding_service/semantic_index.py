import os
import supabase
from sentence_transformers import SentenceTransformer
import faiss
import numpy as np
from dotenv import load_dotenv

load_dotenv()

# Setup
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

supabase_client = supabase.create_client(SUPABASE_URL, SUPABASE_KEY)

# Load model
model = SentenceTransformer('all-MiniLM-L6-v2')

# Step 1: Load data from Supabase
def fetch_combined_data():
    processes = supabase_client.table('processes').select('id, name, description').execute().data
    steps = supabase_client.table('process_steps').select('id, name, description').execute().data
    
    combined = []
    for p in processes:
        combined.append({
            'source': 'process',
            'id': p['id'],
            'name': p['name'],
            'description': p['description']
        })
    for s in steps:
        combined.append({
            'source': 'step',
            'id': s['id'],
            'name': s['name'],
            'description': s['description']
        })
    return combined


# Step 2: Generate embeddings
def embed_processes(processes):
    texts = [f"{p['name']} - {p['description']}" for p in processes]
    embeddings = model.encode(texts)
    return np.array(embeddings).astype('float32')

# Step 3: Index using FAISS
def create_faiss_index(embeddings):
    index = faiss.IndexFlatL2(embeddings.shape[1])
    index.add(embeddings)
    return index

if __name__ == "__main__":
    data = fetch_combined_data()
    embeddings = embed_processes(data)
    index = create_faiss_index(embeddings)
    faiss.write_index(index, "process_index.faiss")
    print("✅ Process index created and saved.")
