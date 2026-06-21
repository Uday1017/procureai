"""
Vector Store — core/vectorstore.py
=====================================
What this does:
  - Saves embedded chunks into ChromaDB (a local vector database)
  - When a question comes in, finds the most relevant chunks
  - Returns the top-K most similar chunks for the LLM to use

What is ChromaDB?
  Think of it as a database where instead of searching by ID or keyword,
  you search by *meaning*. You give it a vector (your question's embedding)
  and it returns the vectors that are mathematically closest — meaning
  they're about the same topic.

Why local (not cloud)?
  For a portfolio project, local ChromaDB is perfect. No API keys, no cost,
  data persists between sessions. In production, Supervity would use
  Vertex AI Vector Search or Pinecone.
"""

import chromadb
from chromadb.config import Settings
from typing import List, Dict
import os


class DocumentVectorStore:
    """
    Wrapper around ChromaDB that handles:
    - Creating/loading a persistent collection
    - Adding embedded document chunks
    - Searching for relevant chunks given a query vector
    """
    
    def __init__(self, persist_directory: str = "./data/vectorstore"):
        """
        Initialize ChromaDB with a local persistence folder.
        Data survives between app restarts — important for demos.
        
        Args:
            persist_directory: folder where ChromaDB saves its data
        """
        os.makedirs(persist_directory, exist_ok=True)
        
        # PersistentClient saves data to disk automatically
        self.client = chromadb.PersistentClient(path=persist_directory)
        
        # A "collection" is like a table in a regular database
        # get_or_create means it loads existing data if it exists
        self.collection = self.client.get_or_create_collection(
            name="procurement_documents",
            metadata={"hnsw:space": "cosine"}  # cosine similarity for text
        )
        
        print(f"✓ Vector store ready — {self.collection.count()} chunks loaded")
    
    def add_document(self, embedded_chunks: List[Dict], doc_name: str):
        """
        Adds all chunks from a document into the vector store.
        
        ChromaDB needs 3 things for each entry:
        - id: unique string identifier
        - embedding: the vector (list of floats)
        - document: the original text (stored for retrieval)
        - metadata: any extra info (doc name, chunk id, etc.)
        
        Args:
            embedded_chunks: output from embed_chunks() in embeddings.py
            doc_name: name of the uploaded file (for metadata)
        """
        ids = []
        embeddings = []
        documents = []
        metadatas = []
        
        for chunk in embedded_chunks:
            # Create a unique ID: docname_chunkid
            chunk_id = f"{doc_name}_chunk_{chunk['chunk_id']}"
            
            ids.append(chunk_id)
            embeddings.append(chunk["embedding"])
            documents.append(chunk["text"])
            metadatas.append({
                "doc_name": doc_name,
                "chunk_id": chunk["chunk_id"],
                "start_char": chunk["start_char"],
                "end_char": chunk["end_char"]
            })
        
        # Add all chunks in one batch call (more efficient)
        self.collection.add(
            ids=ids,
            embeddings=embeddings,
            documents=documents,
            metadatas=metadatas
        )
        
        print(f"✓ Added {len(embedded_chunks)} chunks from '{doc_name}' to vector store")
    
    def search(self, query_embedding: List[float], top_k: int = 5) -> List[Dict]:
        """
        Finds the top-K most relevant chunks for a given query.
        
        ChromaDB computes cosine similarity between the query vector
        and all stored vectors, returns the closest ones.
        
        Args:
            query_embedding: vector from embed_query() in embeddings.py
            top_k: how many chunks to return (5 is a good default)
        
        Returns:
            List of dicts with text, doc_name, similarity score, etc.
        """
        results = self.collection.query(
            query_embeddings=[query_embedding],
            n_results=min(top_k, self.collection.count()),  # Can't return more than we have
            include=["documents", "metadatas", "distances"]
        )
        
        # Reformat ChromaDB's output into something cleaner
        relevant_chunks = []
        
        if results["documents"] and results["documents"][0]:
            for i in range(len(results["documents"][0])):
                relevant_chunks.append({
                    "text": results["documents"][0][i],
                    "doc_name": results["metadatas"][0][i]["doc_name"],
                    "chunk_id": results["metadatas"][0][i]["chunk_id"],
                    "similarity": 1 - results["distances"][0][i]  # Convert distance to similarity
                })
        
        return relevant_chunks
    
    def get_document_count(self) -> int:
        """Returns total number of chunks in the store."""
        return self.collection.count()
    
    def list_documents(self) -> List[str]:
        """Returns list of unique document names in the store."""
        if self.collection.count() == 0:
            return []
        
        results = self.collection.get(include=["metadatas"])
        doc_names = list(set(m["doc_name"] for m in results["metadatas"]))
        return doc_names
    
    def clear_all(self):
        """Wipes the entire vector store. Useful for fresh starts."""
        self.client.delete_collection("procurement_documents")
        self.collection = self.client.get_or_create_collection(
            name="procurement_documents",
            metadata={"hnsw:space": "cosine"}
        )
        print("✓ Vector store cleared")