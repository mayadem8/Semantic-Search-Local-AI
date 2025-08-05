from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import faiss
import numpy as np
from sentence_transformers import SentenceTransformer
from semantic_index import fetch_combined_data, rebuild_faiss_index, supabase_client
from typing import Dict, Any
import time
import asyncio
from contextlib import asynccontextmanager
import threading


@asynccontextmanager
async def lifespan(app: FastAPI):
    asyncio.create_task(async_init())
    yield
    
    
app = FastAPI(lifespan=lifespan)

model = None
index = None
metadata = None


app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class QueryRequest(BaseModel):
    query: str


async def async_init():
    global model, index, metadata
    print("Initializing model and index...")
    model = SentenceTransformer("all-MiniLM-L6-v2")
    index = faiss.read_index("process_index.faiss")
    metadata = fetch_combined_data()
    print("Model and index initialized.")


@app.post("/search")
def search(req: QueryRequest):
    query_embedding = model.encode([req.query])
    query_embedding = np.array(query_embedding).astype("float32")

    D, I = index.search(query_embedding, 10)  # Search more to allow deduping

    raw_results = [
        {**metadata[i], "distance": float(D[0][idx])} for idx, i in enumerate(I[0])
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
                    final_results.append(
                        {
                            "source": "process",
                            "id": parent["id"],
                            "name": parent["name"],
                            "description": parent["description"],
                            "distance": r["distance"],
                            "step_name": r["name"],
                            "step_description": r["description"],
                        }
                    )
                    seen_ids.add(process_id)
        else:
            if r["id"] not in seen_ids:
                final_results.append(
                    {
                        "source": r["source"],
                        "id": r["id"],
                        "name": r["name"],
                        "description": r["description"],
                        "distance": r["distance"],
                        "step_name": None,
                        "step_description": None,
                    }
                )
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
    return {"status": "success", "message": "FAISS index rebuilt and reloaded.", "elapsed_time": elapsed_time}

