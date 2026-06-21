"""
Helpers — utils/helpers.py
============================
Utility functions used across the app.
"""

import os
import itertools
from pathlib import Path
from dotenv import load_dotenv

_keys = None
_key_cycle = None


def load_api_key() -> str:
    """Returns a single key (first available)."""
    load_dotenv()
    for i in range(1, 5):
        key = os.getenv(f"GEMINI_API_KEY_{i}") or os.getenv("GEMINI_API_KEY")
        if key:
            return key
    raise ValueError("No GEMINI_API_KEY found in .env")


def get_next_key() -> str:
    """Rotates through all available keys."""
    global _keys, _key_cycle
    load_dotenv()

    if _key_cycle is None:
        _keys = []
        for i in range(1, 5):
            k = os.getenv(f"GEMINI_API_KEY_{i}")
            if k:
                _keys.append(k)
        if not _keys:
            k = os.getenv("GEMINI_API_KEY")
            if k:
                _keys = [k]
        _key_cycle = itertools.cycle(_keys)

    return next(_key_cycle)


def save_uploaded_file(uploaded_file, upload_dir: str = "./data/uploads") -> str:
    """
    Saves a Streamlit uploaded file object to disk.
    
    Args:
        uploaded_file: st.file_uploader result
        upload_dir: directory to save in
    
    Returns:
        Full path to saved file
    """
    os.makedirs(upload_dir, exist_ok=True)
    
    save_path = os.path.join(upload_dir, uploaded_file.name)
    
    with open(save_path, "wb") as f:
        f.write(uploaded_file.getbuffer())
    
    return save_path


def format_sources_for_display(sources: list) -> str:
    """
    Formats source chunks/URLs for display in Streamlit.
    """
    if not sources:
        return ""
    
    lines = ["**Sources:**"]
    
    for i, source in enumerate(sources[:3]):  # Show max 3 sources
        if isinstance(source, dict):
            if "doc_name" in source:  # RAG source
                sim = source.get("similarity", 0)
                lines.append(f"📄 `{source['doc_name']}` (relevance: {sim:.0%})")
            elif "url" in source:  # Web source
                title = source.get("title", "Web Source")
                url = source.get("url", "")
                if url:
                    lines.append(f"🌐 [{title}]({url})")
                else:
                    lines.append(f"🌐 {title}")
    
    return "\n".join(lines)


def get_method_badge(method: str) -> str:
    """Returns a colored label for the method used."""
    badges = {
        "rag": "📄 Answered from your documents",
        "web_search": "🌐 Answered from web search",
        "web_search_fallback": "🌐 Not in documents — found on web",
        "rag_plus_web": "📄🌐 Combined: documents + web search",
    }
    return badges.get(method, f"🤖 {method}")