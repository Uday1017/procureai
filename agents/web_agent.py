"""
Web Search Agent — agents/web_agent.py
=========================================
What this does:
  - When RAG can't find the answer in uploaded documents,
    this agent searches the web using Gemini's built-in grounding
  - Gemini 2.0 Flash with Google Search grounding pulls live web results
  - Returns an answer with web citations

Why Gemini Grounding instead of a separate search API?
  Gemini 2.0 Flash has native Google Search integration — you don't need
  a separate Tavily or SerpAPI key. Gemini fetches real web results,
  reasons over them, and gives you a cited answer. One API for everything.

  This is also a great talking point in interviews — you understand
  that modern LLMs can be grounded, which is better than naive RAG.
"""

from google import genai
from google.genai import types
from typing import Dict


class WebSearchAgent:
    """
    Agent that searches the web when documents don't have the answer.
    """

    def __init__(self, api_key: str):
        """
        Args:
            api_key: Gemini API key
        """
        self.client = genai.Client(api_key=api_key)
        self.model_name = "gemini-2.5-flash"
        self.tools = [types.Tool(google_search=types.GoogleSearch())]
    
    def search(self, question: str, procurement_context: str = "") -> Dict:
        """
        Searches the web to answer a question.
        
        Args:
            question: the user's question
            procurement_context: optional context from the user's documents
                                 (helps focus the web search)
        
        Returns:
            Dict with:
              - "answer": web-sourced answer
              - "sources": list of URLs Gemini cited
              - "searched_web": True
        """
        
        print(f"\n[WebSearch] Searching web for: {question}")
        
        # Build a focused prompt for procurement context
        if procurement_context:
            prompt = f"""I'm analyzing a procurement document with this context:
{procurement_context}

The document doesn't contain the answer to this question:
{question}

Please search the web and provide current, accurate information to answer this question.
Focus on procurement, supply chain, and enterprise business contexts where relevant.
Cite your sources."""
        else:
            prompt = f"""Search the web for current information to answer this procurement/business question:

{question}

Provide a clear, accurate answer with sources. Focus on enterprise and business contexts."""
        
        response = self.client.models.generate_content(
            model=self.model_name,
            contents=prompt,
            config=types.GenerateContentConfig(tools=self.tools)
        )
        
        # Extract any grounding metadata (URLs Gemini used)
        sources = []
        if hasattr(response, 'candidates') and response.candidates:
            candidate = response.candidates[0]
            if hasattr(candidate, 'grounding_metadata') and candidate.grounding_metadata:
                meta = candidate.grounding_metadata
                if hasattr(meta, 'grounding_chunks'):
                    for chunk in meta.grounding_chunks:
                        if hasattr(chunk, 'web') and chunk.web:
                            sources.append({
                                "title": getattr(chunk.web, 'title', 'Web Source'),
                                "url": getattr(chunk.web, 'uri', '')
                            })
        
        answer_text = response.text
        print(f"[WebSearch] ✓ Found answer from web ({len(sources)} sources cited)")
        
        return {
            "answer": answer_text,
            "sources": sources,
            "searched_web": True
        }