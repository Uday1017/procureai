"""
RAG Agent — agents/rag_agent.py
==================================
What this does:
  - Takes a user question
  - Embeds it into a vector
  - Searches the vector store for relevant chunks
  - Feeds those chunks + the question to Gemini
  - Returns a grounded answer (with source document info)

What is RAG?
  Retrieval Augmented Generation. Instead of asking the LLM to answer
  from memory (which leads to hallucinations), we RETRIEVE relevant
  context from our documents first, then AUGMENT the LLM prompt with
  that context, then let it GENERATE an answer.

  Memory-only LLM: "What's the delivery date?" → makes something up
  RAG LLM:         "What's the delivery date?" → finds the clause in
                    the contract → answers accurately with source
"""

from google import genai
from core.embeddings import embed_query
from core.vectorstore import DocumentVectorStore
from utils.helpers import get_next_key
from typing import Dict


class RAGAgent:
    """
    The core question-answering agent that works from uploaded documents.
    """
    
    def __init__(self, api_key: str, vectorstore: DocumentVectorStore):
        """
        Args:
            api_key: Gemini API key
            vectorstore: initialized DocumentVectorStore instance
        """
        self.api_key = api_key
        self.vectorstore = vectorstore
        self.client = genai.Client(api_key=api_key)
    
    def answer(self, question: str, top_k: int = 5) -> Dict:
        """
        Full RAG pipeline: question → embed → retrieve → generate.
        
        Args:
            question: user's question in plain English
            top_k: how many document chunks to retrieve
        
        Returns:
            Dict with:
              - "answer": the LLM's response
              - "sources": which chunks were used
              - "confidence": high/medium/low based on similarity scores
              - "found_in_docs": True/False
        """
        
        # Step 1: Embed the question
        print(f"\n[RAG] Question: {question}")
        query_vector = embed_query(question, get_next_key())
        
        # Step 2: Search vector store for relevant chunks
        relevant_chunks = self.vectorstore.search(query_vector, top_k=top_k)
        
        if not relevant_chunks:
            return {
                "answer": None,
                "sources": [],
                "confidence": "none",
                "found_in_docs": False
            }
        
        # Step 3: Check if the results are actually relevant
        # If the best match has low similarity, the doc probably doesn't have the answer
        best_similarity = relevant_chunks[0]["similarity"]
        print(f"[RAG] Best similarity score: {best_similarity:.2f}")
        
        if best_similarity < 0.4:  # Threshold — tune this based on testing
            return {
                "answer": None,
                "sources": relevant_chunks,
                "confidence": "low",
                "found_in_docs": False
            }
        
        # Step 4: Build a context string from retrieved chunks
        context_parts = []
        for i, chunk in enumerate(relevant_chunks):
            context_parts.append(
                f"[Source {i+1} — from '{chunk['doc_name']}' (relevance: {chunk['similarity']:.0%})]:\n{chunk['text']}"
            )
        context = "\n\n".join(context_parts)
        
        # Step 5: Send to Gemini with a carefully crafted prompt
        prompt = f"""You are a procurement document expert helping enterprise teams analyze contracts, invoices, and RFQs.

DOCUMENT CONTEXT (retrieved from uploaded documents):
{context}

USER QUESTION: {question}

Instructions:
- Answer ONLY based on the document context above
- Be specific — include exact numbers, dates, codes from the documents
- If the context has a table with the answer, format it clearly
- Cite which source document your answer came from
- If you're not sure, say "The documents mention X but don't explicitly state Y"
- Do NOT make up information not present in the context

Answer:"""
        
        response = self.client.models.generate_content(
            model="gemini-2.5-flash",
            contents=prompt
        )
        answer_text = response.text
        
        # Determine confidence based on similarity score
        if best_similarity > 0.75:
            confidence = "high"
        elif best_similarity > 0.55:
            confidence = "medium"
        else:
            confidence = "low"
        
        print(f"[RAG] ✓ Answer generated (confidence: {confidence})")
        
        return {
            "answer": answer_text,
            "sources": relevant_chunks,
            "confidence": confidence,
            "found_in_docs": True
        }