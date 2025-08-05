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
    processes = supabase_client.table('processes') \
    .select('id, name, description, pain_points') \
    .eq('archived', False) \
    .execute().data

    steps = supabase_client.table('process_steps') \
        .select('id, name, description, pain_points, process_id') \
        .execute().data

    
    combined = []
    for p in processes:
        combined.append({
            'source': 'process',
            'id': p['id'],
            'name': p['name'],
            'description': p['description'],
            'pain_points': p.get('pain_points') or []
        })
    for s in steps:
        combined.append({
            'source': 'step',
            'id': s['id'],
            'name': s['name'],
            'description': s['description'],
            'pain_points': s.get('pain_points') or [],
            'process_id': s['process_id']
        })

    return combined


# Step 2: Generate embeddings
def embed_processes(processes):
    texts = []
    for p in processes:
        pain_points = p.get('pain_points') or []
        if isinstance(pain_points, list):
            pain_points_text = " ".join(pain_points)
        else:
            pain_points_text = str(pain_points)
        texts.append(f"{p['name']} - {p['description']} {pain_points_text}")
    embeddings = model.encode(texts)
    return np.array(embeddings).astype('float32')


# Step 3: Index using FAISS
def create_faiss_index(embeddings):
    index = faiss.IndexFlatL2(embeddings.shape[1])
    index.add(embeddings)
    return index


def rebuild_faiss_index():
    data = fetch_combined_data()
    embeddings = embed_processes(data)
    index = create_faiss_index(embeddings)
    faiss.write_index(index, "process_index.faiss")
    return index, data


if __name__ == "__main__":
    index, data = rebuild_faiss_index()
    print("✅ Process index created and saved.")
