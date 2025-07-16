import faiss
import numpy as np
from sentence_transformers import SentenceTransformer
from semantic_index import fetch_combined_data  # reuse function
import os

# Load saved index
index = faiss.read_index("process_index.faiss")

# Load model
model = SentenceTransformer('sentence-transformers/multi-qa-MiniLM-L6-cos-v1')


# Load process metadata
processes = fetch_combined_data()

# === 1. Get user query ===
query = input("🔍 Enter a process-related search query: ")

# === 2. Convert query to embedding ===
query_embedding = model.encode([query]).astype('float32')

# === 3. Search FAISS index ===
k = 3  # top 3 results
D, I = index.search(query_embedding, k)

# === 4. Print results ===
print("\n📌 Top matching processes:")
for i in I[0]:
    print(f"\n➡️ {processes[i]['name']}\n📝 {processes[i]['description']}")
