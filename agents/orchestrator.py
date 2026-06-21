"""
Orchestrator — agents/orchestrator.py
========================================
What this does:
  - Acts as the "brain" that decides which agent to call
  - Tries RAG first (document search)
  - If RAG is confident → returns that answer
  - If RAG is low confidence → falls back to web search
  - Can also combine both answers for complex questions

Why an orchestrator?
  In real enterprise AI (which is what Supervity builds), you rarely have
  just one agent. You have multiple specialized agents and a router that
  decides which one(s) to call. This is called an "agentic architecture"
  and it's a core concept Supervity looks for.

  Supervity's AI employees work the same way — a Procurement Specialist
  agent routes queries to supplier databases, ERP systems, or web search
  depending on what's being asked.
"""

from google import genai
from agents.rag_agent import RAGAgent
from agents.web_agent import WebSearchAgent
from core.vectorstore import DocumentVectorStore
from utils.helpers import get_next_key
from typing import Dict


class ProcurementOrchestrator:
    """
    The main orchestrator — decides RAG vs Web vs Both.
    This is what the Streamlit UI calls directly.
    """
    
    def __init__(self, api_key: str, vectorstore: DocumentVectorStore):
        """
        Args:
            api_key: Gemini API key
            vectorstore: shared DocumentVectorStore instance
        """
        self.api_key = api_key
        self.rag_agent = RAGAgent(api_key, vectorstore)
        self.web_agent = WebSearchAgent(api_key)
        self.vectorstore = vectorstore
        self.client = genai.Client(api_key=get_next_key())
    
    def classify_question(self, question: str) -> str:
        """
        Uses Gemini to classify whether this question needs:
        - "rag_only": answer is likely in the uploaded documents
        - "web_only": needs current/market data not in any document
        - "both": needs both document context AND web info
        
        This is a mini LLM call — fast and cheap with Flash.
        """
        prompt = f"""Classify this question for a procurement AI system.
        
Question: "{question}"

Respond with ONLY one of these three labels:
- "rag_only" — if the answer is likely in uploaded documents (invoices, contracts, RFQs, specs)
- "web_only" — if the answer needs current market data, prices, regulations, or company info
- "both" — if it needs both document context AND web research

Examples:
"What's the delivery date in this contract?" → rag_only
"What's the current steel price per ton?" → web_only  
"Is the price in this invoice reasonable for current market?" → both

Label:"""
        
        response = self.client.models.generate_content(
            model="gemini-2.5-flash",
            contents=prompt
        )
        label = response.text.strip().lower().replace('"', '').replace("'", "")
        
        # Sanitize response
        if "web_only" in label:
            return "web_only"
        elif "both" in label:
            return "both"
        else:
            return "rag_only"
    
    def answer(self, question: str) -> Dict:
        """
        Main entry point — takes a question, returns a complete answer.
        
        Decision logic:
        1. If no documents uploaded → go straight to web
        2. Classify the question type
        3. Try RAG if appropriate
        4. Fall back to web if RAG confidence is low
        5. Combine if "both" classification
        
        Returns:
            Dict with answer, sources, method used, and metadata
        """
        print(f"\n{'='*50}")
        print(f"[Orchestrator] Processing: {question}")
        
        has_documents = self.vectorstore.get_document_count() > 0
        
        # No documents loaded — go straight to web search
        if not has_documents:
            print("[Orchestrator] No documents in store → Web search")
            result = self.web_agent.search(question)
            result["method"] = "web_search"
            result["reason"] = "No documents uploaded — searched the web"
            return result
        
        # Classify the question
        question_type = self.classify_question(question)
        print(f"[Orchestrator] Question type: {question_type}")
        
        if question_type == "web_only":
            # Needs web data — skip RAG
            result = self.web_agent.search(question)
            result["method"] = "web_search"
            result["reason"] = "Question requires current web data"
            return result
        
        elif question_type == "rag_only":
            # Try RAG first
            rag_result = self.rag_agent.answer(question)
            
            if rag_result["found_in_docs"] and rag_result["confidence"] in ["high", "medium"]:
                rag_result["method"] = "rag"
                rag_result["reason"] = f"Found in documents (confidence: {rag_result['confidence']})"
                return rag_result
            else:
                # RAG didn't find it — fall back to web
                print("[Orchestrator] RAG low confidence → falling back to web")
                result = self.web_agent.search(question)
                result["method"] = "web_search_fallback"
                result["reason"] = "Not found in documents — searched the web"
                return result
        
        else:  # "both"
            # Get document context first, then enhance with web
            print("[Orchestrator] Using both RAG + Web")
            rag_result = self.rag_agent.answer(question)
            
            # Get doc context to help focus web search
            doc_context = ""
            if rag_result["found_in_docs"] and rag_result["answer"]:
                doc_context = f"From uploaded documents: {rag_result['answer'][:500]}"
            
            web_result = self.web_agent.search(question, procurement_context=doc_context)
            
            # Combine both answers with Gemini
            combined_prompt = f"""Synthesize these two answers into one comprehensive response:

FROM DOCUMENTS:
{rag_result.get('answer', 'Not found in documents')}

FROM WEB SEARCH:
{web_result.get('answer', 'No web results')}

USER QUESTION: {question}

Provide a single, clear, well-structured answer that combines insights from both sources.
Clearly indicate when information comes from the uploaded document vs. current market data."""
            
            combined_response = self.client.models.generate_content(
                model="gemini-2.5-flash",
                contents=combined_prompt
            )
            
            return {
                "answer": combined_response.text,
                "sources": rag_result.get("sources", []) + web_result.get("sources", []),
                "method": "rag_plus_web",
                "reason": "Combined document analysis with live web data",
                "confidence": rag_result.get("confidence", "medium"),
                "found_in_docs": rag_result.get("found_in_docs", False)
            }