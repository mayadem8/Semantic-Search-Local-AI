from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import faiss
import numpy as np
from sentence_transformers import SentenceTransformer
from semantic_index import fetch_combined_data, supabase_client


app = FastAPI()


app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, restrict this
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class QueryRequest(BaseModel):
    query: str


model = SentenceTransformer('sentence-transformers/multi-qa-MiniLM-L6-cos-v1')
index = faiss.read_index("process_index.faiss")
metadata = fetch_combined_data()

@app.post("/search")
def search(req: QueryRequest):
    query_embedding = model.encode([req.query]).astype('float32')
    D, I = index.search(query_embedding, 3)
    
    raw_results = [metadata[i] for i in I[0]]
    final_results = []

    # Load processes once to avoid repeated Supabase calls
    all_processes = {p['id']: p for p in supabase_client.table('processes').select('id, name, description').execute().data}

    for r in raw_results:
        if r['source'] == 'step':
            parent_process = all_processes.get(r.get('process_id'))
            if parent_process:
                final_results.append({
                    'source': 'process',
                    'id': parent_process['id'],
                    'name': parent_process['name'],
                    'description': parent_process['description']
                })
        else:
            final_results.append(r)
    
    return final_results

