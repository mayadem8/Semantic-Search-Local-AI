from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import faiss
import numpy as np
from sentence_transformers import SentenceTransformer
from semantic_index import fetch_combined_data

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
    results = [metadata[i] for i in I[0]]
    return results
