"""
Embeddings — core/embeddings.py
=================================
What this does:
  - Takes the extracted text and splits it into chunks
  - Converts each chunk into a "vector" (a list of ~768 numbers)
  - These vectors capture the *meaning* of the text
  - Similar meaning = similar vectors (close together in math space)

Why do we chunk?
  Gemini can only process a limited amount of text at once for embeddings.
  Also, smaller chunks = more precise retrieval. If you embed the whole
  document as one blob, you can't pinpoint which part answers the question.

Why Gemini Embeddings?
  We're using the same Google ecosystem throughout — this means the
  embedding space is consistent with the LLM that will read the results.
"""

from google import genai
from utils.helpers import get_next_key
from typing import List, Dict
import re
import time


def chunk_text(text: str, chunk_size: int = 800, overlap: int = 100) -> List[Dict]:
    """
    Splits a long text into overlapping chunks.
    
    Why overlap? So that if an answer spans two chunks (e.g., a sentence
    starts at the end of chunk 1 and finishes at the start of chunk 2),
    we don't lose the context.
    
    Args:
        text: the full extracted text from OCR
        chunk_size: how many characters per chunk (800 is a good default)
        overlap: how many characters to repeat between consecutive chunks
    
    Returns:
        List of dicts: [{"text": "...", "chunk_id": 0, "start": 0}, ...]
    """
    chunks = []
    start = 0
    chunk_id = 0
    
    # Clean up excessive whitespace first
    text = re.sub(r'\n{3,}', '\n\n', text)
    text = text.strip()
    
    while start < len(text):
        end = start + chunk_size
        
        # Don't cut mid-sentence — find the nearest sentence end
        if end < len(text):
            # Look for a period, newline, or question mark to end on
            for punct in ['. ', '\n', '? ', '! ']:
                last_punct = text.rfind(punct, start, end)
                if last_punct != -1:
                    end = last_punct + len(punct)
                    break
        
        chunk_text_content = text[start:end].strip()
        
        if chunk_text_content:  # Skip empty chunks
            chunks.append({
                "text": chunk_text_content,
                "chunk_id": chunk_id,
                "start_char": start,
                "end_char": end
            })
            chunk_id += 1
        
        # Move forward but keep overlap
        start = end - overlap
    
    print(f"✓ Text split into {len(chunks)} chunks")
    return chunks


def embed_chunks(chunks: List[Dict], api_key: str) -> List[Dict]:
    """
    Converts each text chunk into a vector using Gemini Embeddings.
    
    The model "models/gemini-embedding-001" is Google's latest embedding model.
    It produces 768-dimensional vectors.
    
    task_type="RETRIEVAL_DOCUMENT" tells Gemini these are documents being
    indexed, not questions being asked. This matters — embeddings are
    optimized differently for documents vs queries.
    
    Args:
        chunks: list of chunk dicts from chunk_text()
        api_key: Gemini API key
    
    Returns:
        Same list but each dict now has an "embedding" key with the vector
    """
    client = genai.Client(api_key=get_next_key())
    embedded_chunks = []
    
    for i, chunk in enumerate(chunks):
        result = client.models.embed_content(
            model="models/gemini-embedding-001",
            contents=chunk["text"],
        )
        
        chunk_with_embedding = chunk.copy()
        chunk_with_embedding["embedding"] = result.embeddings[0].values
        embedded_chunks.append(chunk_with_embedding)
        time.sleep(0.5)
        
        if (i + 1) % 10 == 0:
            print(f"  Embedded {i + 1}/{len(chunks)} chunks...")
    
    print(f"✓ All {len(embedded_chunks)} chunks embedded (768-dim vectors)")
    return embedded_chunks


def embed_query(query: str, api_key: str) -> List[float]:
    """
    Embeds a user's question for retrieval.
    
    Note: task_type is "RETRIEVAL_QUERY" here (not DOCUMENT).
    This is important — Google optimizes query embeddings differently
    so they point toward relevant document embeddings.
    
    Args:
        query: the user's question string
        api_key: Gemini API key
    
    Returns:
        768-dimensional vector (list of floats)
    """
    client = genai.Client(api_key=get_next_key())
    result = client.models.embed_content(
        model="models/gemini-embedding-001",
        contents=query,
    )
    return result.embeddings[0].values