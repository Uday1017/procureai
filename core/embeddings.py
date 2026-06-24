from google import genai
from typing import List, Dict
import re
import time
import os
from dotenv import load_dotenv
import itertools

_key_cycle = None

def _get_key():
    global _key_cycle
    if _key_cycle is None:
        load_dotenv()
        keys = [os.getenv(f"GEMINI_API_KEY_{i}") for i in range(1, 5)]
        keys = [k for k in keys if k]
        if not keys:
            k = os.getenv("GEMINI_API_KEY")
            if k:
                keys = [k]
        _key_cycle = itertools.cycle(keys)
    return next(_key_cycle)


def chunk_text(text: str, chunk_size: int = 600, overlap: int = 50) -> List[Dict]:
    """Smaller chunks = fewer API calls = less memory."""
    chunks = []
    start = 0
    chunk_id = 0

    text = re.sub(r'\n{3,}', '\n\n', text).strip()

    while start < len(text):
        end = start + chunk_size
        if end < len(text):
            for punct in ['. ', '\n', '? ', '! ']:
                last_punct = text.rfind(punct, start, end)
                if last_punct != -1:
                    end = last_punct + len(punct)
                    break

        chunk_content = text[start:end].strip()
        if chunk_content:
            chunks.append({
                "text": chunk_content,
                "chunk_id": chunk_id,
                "start_char": start,
                "end_char": end
            })
            chunk_id += 1
        start = end - overlap

    print(f"✓ Text split into {len(chunks)} chunks")
    return chunks


def embed_and_store_chunks(chunks: List[Dict], doc_name: str, vectorstore, api_key: str):
    """
    Embeds ONE chunk at a time and immediately stores it.
    Never holds all vectors in memory at once.
    This prevents the RAM spike that was killing the process.
    """
    client = genai.Client(api_key=api_key)

    print(f"Embedding and storing {len(chunks)} chunks one by one...")

    for i, chunk in enumerate(chunks):
        # Embed one chunk
        result = client.models.embed_content(
            model="models/gemini-embedding-001",
            contents=chunk["text"],
            config={"output_dimensionality": 768}
        )
        embedding = result.embeddings[0].values

        # Immediately store it — don't accumulate in a list
        vectorstore.add_single_chunk(
            text=chunk["text"],
            embedding=embedding,
            doc_name=doc_name,
            chunk_id=chunk["chunk_id"],
            start_char=chunk["start_char"],
            end_char=chunk["end_char"]
        )

        # Free memory
        del embedding
        del result

        print(f"  ✓ Chunk {i+1}/{len(chunks)} embedded and stored")
        time.sleep(0.3)  # Avoid rate limit

    print(f"✓ All {len(chunks)} chunks processed")


def embed_query(query: str, api_key: str) -> List[float]:
    """Embeds a user question for retrieval."""
    client = genai.Client(api_key=api_key)

    result = client.models.embed_content(
        model="models/gemini-embedding-001",
        contents=query,
        config={"output_dimensionality": 768}
    )
    return result.embeddings[0].values