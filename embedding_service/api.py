import os
import time
import asyncio
from contextlib import asynccontextmanager
from typing import Dict, Any

import faiss
import numpy as np
import supabase
from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from sentence_transformers import SentenceTransformer
from fastapi.responses import HTMLResponse

# --- Load ENV ---
load_dotenv()
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

# --- Setup Supabase ---
supabase_client = supabase.create_client(SUPABASE_URL, SUPABASE_KEY)

# --- Model & Index ---
model = None
index = None
metadata = None

# --- FastAPI ---
@asynccontextmanager
async def lifespan(app: FastAPI):
    asyncio.create_task(async_init())
    yield

app = FastAPI(lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class QueryRequest(BaseModel):
    query: str

# ---------------------- Semantic Index Functions ----------------------

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

def embed_processes(processes):
    texts = []
    for p in processes:
        pain_points = p.get('pain_points') or []
        pain_points_text = " ".join(pain_points) if isinstance(pain_points, list) else str(pain_points)
        texts.append(f"{p['name']} - {p['description']} {pain_points_text}")
    embeddings = model.encode(texts)
    return np.array(embeddings).astype('float32')

def create_faiss_index(embeddings):
    index = faiss.IndexFlatL2(embeddings.shape[1])
    index.add(embeddings)
    return index

def rebuild_faiss_index():
    data = fetch_combined_data()
    embeddings = embed_processes(data)
    new_index = create_faiss_index(embeddings)
    faiss.write_index(new_index, "process_index.faiss")
    return new_index, data

# ---------------------- Init ----------------------

async def async_init():
    global model, index, metadata
    print("Initializing model and index...")
    model = SentenceTransformer("all-MiniLM-L6-v2")
    if os.path.exists("process_index.faiss"):
        index = faiss.read_index("process_index.faiss")
        metadata = fetch_combined_data()
    else:
        index, metadata = rebuild_faiss_index()
    print("Model and index initialized.")

# ---------------------- API Endpoints ----------------------

@app.post("/search")
def search(req: QueryRequest):
    query_embedding = model.encode([req.query])
    query_embedding = np.array(query_embedding).astype("float32")

    D, I = index.search(query_embedding, 10)  # search top 10
    raw_results = [
        {**metadata[i], "distance": float(D[0][idx])}
        for idx, i in enumerate(I[0])
    ]

    response = supabase_client.table('processes') \
        .select('id, name, description') \
        .eq('archived', False) \
        .execute()
    all_processes: Dict[int, Dict[str, Any]] = {p['id']: p for p in response.data}

    seen_ids = set()
    final_results = []
    for r in raw_results:
        if r["source"] == "step":
            process_id = r.get("process_id")
            if process_id and process_id not in seen_ids:
                parent = all_processes.get(process_id)
                if parent:
                    final_results.append({
                        "source": "process",
                        "id": parent["id"],
                        "name": parent["name"],
                        "description": parent["description"],
                        "distance": r["distance"],
                        "step_name": r["name"],
                        "step_description": r["description"],
                    })
                    seen_ids.add(process_id)
        else:
            if r["id"] not in seen_ids:
                final_results.append({
                    "source": r["source"],
                    "id": r["id"],
                    "name": r["name"],
                    "description": r["description"],
                    "distance": r["distance"],
                    "step_name": None,
                    "step_description": None,
                })
                seen_ids.add(r["id"])

    final_results.sort(key=lambda x: x["distance"])
    simplified = [{"id": r["id"], "distance": r["distance"]} for r in final_results]
    return simplified

@app.post("/rebuild-index")
def rebuild_index():
    global index, metadata
    start_time = time.time()
    index, metadata = rebuild_faiss_index()
    elapsed_time = time.time() - start_time
    return {
        "status": "success",
        "message": "FAISS index rebuilt and reloaded.",
        "elapsed_time": elapsed_time
    }

@app.get("/")
def root():
    return HTMLResponse("Semantic Search API is running.")