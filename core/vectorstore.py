"""
Vector Store — core/vectorstore.py
Lightweight numpy-based vector store — no ChromaDB, no memory bloat.
Stores vectors in a plain JSON file, searches with cosine similarity.
"""

import json
import os
import numpy as np
from typing import List, Dict


class DocumentVectorStore:

    def __init__(self, persist_directory: str = "./data/vectorstore"):
        os.makedirs(persist_directory, exist_ok=True)
        self._store_path = os.path.join(persist_directory, "store.json")
        self._chunks: List[Dict] = []
        self._load()
        print(f"✓ Vector store ready — {len(self._chunks)} chunks loaded")

    def _load(self):
        if os.path.exists(self._store_path):
            with open(self._store_path, "r") as f:
                self._chunks = json.load(f)

    def _save(self):
        with open(self._store_path, "w") as f:
            json.dump(self._chunks, f)

    def add_document(self, embedded_chunks: List[Dict], doc_name: str):
        for chunk in embedded_chunks:
            self._chunks.append({
                "text": chunk["text"],
                "embedding": chunk["embedding"],
                "doc_name": doc_name,
                "chunk_id": chunk["chunk_id"],
            })
        self._save()
        print(f"✓ Added {len(embedded_chunks)} chunks from '{doc_name}' to vector store")

    def add_single_chunk(self, text: str, embedding: List[float], doc_name: str,
                         chunk_id: int, start_char: int = 0, end_char: int = 0):
        self._chunks.append({
            "text": text,
            "embedding": embedding,
            "doc_name": doc_name,
            "chunk_id": chunk_id,
        })
        self._save()

    def search(self, query_embedding: List[float], top_k: int = 5) -> List[Dict]:
        if not self._chunks:
            return []

        q = np.array(query_embedding, dtype=np.float32)
        q /= np.linalg.norm(q) + 1e-10

        scores = []
        for chunk in self._chunks:
            v = np.array(chunk["embedding"], dtype=np.float32)
            v /= np.linalg.norm(v) + 1e-10
            scores.append(float(np.dot(q, v)))

        top_indices = np.argsort(scores)[::-1][:top_k]

        return [
            {
                "text": self._chunks[i]["text"],
                "doc_name": self._chunks[i]["doc_name"],
                "chunk_id": self._chunks[i]["chunk_id"],
                "similarity": scores[i],
            }
            for i in top_indices
        ]

    def get_document_count(self) -> int:
        return len(self._chunks)

    def list_documents(self) -> List[str]:
        return list({c["doc_name"] for c in self._chunks})

    def clear_all(self):
        self._chunks = []
        if os.path.exists(self._store_path):
            os.remove(self._store_path)
        print("✓ Vector store cleared")
