"""
Main Streamlit App — ui/app.py
================================
The complete UI for ProcureAI.
Run this with: streamlit run ui/app.py
"""

import streamlit as st
import sys
import os
import base64

# Add project root to path so imports work
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils.helpers import load_api_key, save_uploaded_file, format_sources_for_display, get_method_badge
from core.ocr import extract_text_from_pdf
from core.embeddings import chunk_text, embed_chunks
from core.vectorstore import DocumentVectorStore
from agents.orchestrator import ProcurementOrchestrator
from agents.voice_agent import VoiceAgent

# ─────────────────────────────────────────
# PAGE CONFIG
# ─────────────────────────────────────────
st.set_page_config(
    page_title="ProcureAI — Intelligent Document Agent",
    page_icon="📋",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ─────────────────────────────────────────
# CUSTOM CSS
# ─────────────────────────────────────────
st.markdown("""
<style>
    .main-header {
        background: linear-gradient(135deg, #1a1a2e 0%, #16213e 50%, #0f3460 100%);
        padding: 2rem;
        border-radius: 12px;
        margin-bottom: 2rem;
        text-align: center;
        color: white;
    }
    .main-header h1 { font-size: 2.2rem; margin: 0; }
    .main-header p { opacity: 0.8; margin: 0.5rem 0 0; }
    
    .answer-box {
        background: #f8f9ff;
        border-left: 4px solid #4f46e5;
        padding: 1.5rem;
        border-radius: 0 8px 8px 0;
        margin: 1rem 0;
    }
    .method-badge {
        display: inline-block;
        background: #e0e7ff;
        color: #4f46e5;
        padding: 0.25rem 0.75rem;
        border-radius: 20px;
        font-size: 0.85rem;
        margin-bottom: 1rem;
    }
    .stButton button {
        border-radius: 8px;
        font-weight: 600;
    }
    .upload-section {
        border: 2px dashed #c7d2fe;
        border-radius: 12px;
        padding: 1.5rem;
        text-align: center;
        background: #fafafe;
    }
</style>
""", unsafe_allow_html=True)

# ─────────────────────────────────────────
# SESSION STATE INITIALIZATION
# Streamlit re-runs the whole script on every interaction,
# so we use st.session_state to persist data between runs.
# ─────────────────────────────────────────
if "vectorstore" not in st.session_state:
    st.session_state.vectorstore = None
if "orchestrator" not in st.session_state:
    st.session_state.orchestrator = None
if "voice_agent" not in st.session_state:
    st.session_state.voice_agent = None
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []
if "api_key" not in st.session_state:
    st.session_state.api_key = None
if "docs_loaded" not in st.session_state:
    st.session_state.docs_loaded = []


def initialize_agents(api_key: str):
    """Initialize all agents with the provided API key."""
    vectorstore = DocumentVectorStore(persist_directory="./data/vectorstore")
    orchestrator = ProcurementOrchestrator(api_key, vectorstore)
    voice_agent = VoiceAgent(api_key)
    
    st.session_state.vectorstore = vectorstore
    st.session_state.orchestrator = orchestrator
    st.session_state.voice_agent = voice_agent
    st.session_state.api_key = api_key


def process_uploaded_pdf(pdf_path: str, doc_name: str, api_key: str):
    """Full pipeline: PDF → OCR → Chunk → Embed → Store."""
    
    with st.spinner(f"🔍 Running OCR on {doc_name}..."):
        extracted_text = extract_text_from_pdf(pdf_path, api_key)
    
    with st.spinner("✂️ Splitting into chunks..."):
        chunks = chunk_text(extracted_text, chunk_size=800, overlap=100)
    
    with st.spinner(f"🧠 Generating embeddings for {len(chunks)} chunks..."):
        embedded_chunks = embed_chunks(chunks, api_key)
    
    with st.spinner("💾 Storing in vector database..."):
        st.session_state.vectorstore.add_document(embedded_chunks, doc_name)
    
    return len(chunks), extracted_text


# ─────────────────────────────────────────
# HEADER
# ─────────────────────────────────────────
st.markdown("""
<div class="main-header">
    <h1>📋 ProcureAI</h1>
    <p>Intelligent Document Agent — Talk to your procurement documents</p>
</div>
""", unsafe_allow_html=True)

# ─────────────────────────────────────────
# SIDEBAR
# ─────────────────────────────────────────
with st.sidebar:
    st.markdown("## ⚙️ Setup")
    
    # API Key input
    api_key_input = st.text_input(
        "Gemini API Key",
        type="password",
        placeholder="AIza...",
        help="Get your free key at aistudio.google.com"
    )
    
    if api_key_input and api_key_input != st.session_state.api_key:
        try:
            initialize_agents(api_key_input)
            st.success("✅ Connected to Gemini!")
        except Exception as e:
            st.error(f"❌ Failed: {e}")
    
    # Try loading from .env if no key entered
    if not st.session_state.api_key:
        try:
            env_key = load_api_key()
            initialize_agents(env_key)
            st.info("🔑 Key loaded from .env")
        except:
            pass
    
    st.divider()
    
    # Document upload section
    st.markdown("## 📂 Upload Documents")
    
    if not st.session_state.api_key:
        st.warning("Enter your API key first")
    else:
        uploaded_files = st.file_uploader(
            "Upload PDFs",
            type=["pdf"],
            accept_multiple_files=True,
            help="Invoices, RFQs, contracts, tender documents"
        )
        
        if uploaded_files:
            for uploaded_file in uploaded_files:
                if uploaded_file.name not in st.session_state.docs_loaded:
                    if st.button(f"Process: {uploaded_file.name}", key=f"proc_{uploaded_file.name}"):
                        save_path = save_uploaded_file(uploaded_file)
                        
                        try:
                            num_chunks, raw_text = process_uploaded_pdf(
                                save_path,
                                uploaded_file.name,
                                st.session_state.api_key
                            )
                            st.session_state.docs_loaded.append(uploaded_file.name)
                            st.success(f"✅ Processed! {num_chunks} chunks indexed")
                            
                            with st.expander("👁️ View extracted text"):
                                st.text_area("Raw OCR output", raw_text[:2000] + "...", height=200)
                        except Exception as e:
                            st.error(f"Error: {e}")
    
    st.divider()
    
    # Loaded documents status
    if st.session_state.docs_loaded:
        st.markdown("## 📚 Indexed Documents")
        for doc in st.session_state.docs_loaded:
            st.markdown(f"✅ {doc}")
        
        if st.session_state.vectorstore:
            count = st.session_state.vectorstore.get_document_count()
            st.caption(f"{count} total chunks in vector store")
        
        if st.button("🗑️ Clear All Documents"):
            st.session_state.vectorstore.clear_all()
            st.session_state.docs_loaded = []
            st.session_state.chat_history = []
            st.rerun()
    
    st.divider()
    st.markdown("**Built with:**")
    st.markdown("🤖 Gemini 2.0 Flash · Vision · Embeddings")
    st.markdown("🗄️ ChromaDB · 🎙️ gTTS")

# ─────────────────────────────────────────
# MAIN CONTENT AREA
# ─────────────────────────────────────────

if not st.session_state.api_key:
    # Onboarding state — no API key yet
    st.info("👈 Enter your Gemini API key in the sidebar to get started")
    
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.markdown("### 📄 OCR\nUpload scanned PDFs — Gemini Vision extracts all text including tables")
    with col2:
        st.markdown("### 🧠 RAG\nAsk questions — get answers grounded in your actual documents")
    with col3:
        st.markdown("### 🌐 Web Search\nWhen documents don't have the answer, Gemini searches the web")
    with col4:
        st.markdown("### 🎙️ Voice\nSpeak your questions, hear the answers read back to you")

else:
    # Main chat interface
    tab1, tab2 = st.tabs(["💬 Chat Interface", "🎙️ Voice Mode"])
    
    with tab1:
        st.markdown("### Ask anything about your documents")
        
        # Sample questions
        if not st.session_state.chat_history:
            st.markdown("**Try asking:**")
            sample_questions = [
                "What is the total amount in this invoice?",
                "What are the payment terms?",
                "What's the delivery deadline?",
                "What's the current market price for this material?",
                "Is the price in this invoice reasonable for current market?"
            ]
            cols = st.columns(len(sample_questions))
            for i, q in enumerate(sample_questions):
                with cols[i]:
                    if st.button(q, key=f"sample_{i}", use_container_width=True):
                        st.session_state.pending_question = q
        
        # Chat history display
        for msg in st.session_state.chat_history:
            with st.chat_message(msg["role"]):
                if msg["role"] == "assistant":
                    badge = get_method_badge(msg.get("method", ""))
                    st.markdown(f'<span class="method-badge">{badge}</span>', unsafe_allow_html=True)
                st.markdown(msg["content"])
                if msg.get("sources_text"):
                    st.markdown(msg["sources_text"])
                if msg.get("audio_path") and os.path.exists(msg["audio_path"]):
                    st.audio(msg["audio_path"], format="audio/mp3")
        
        # Question input
        pending = st.session_state.pop("pending_question", None)
        question = st.chat_input("Ask about your documents...") or pending
        
        if question:
            if not st.session_state.orchestrator:
                st.error("Please enter your API key first")
            else:
                # Add user message
                st.session_state.chat_history.append({
                    "role": "user",
                    "content": question
                })
                
                with st.chat_message("user"):
                    st.markdown(question)
                
                # Get answer
                with st.chat_message("assistant"):
                    with st.spinner("🤔 Thinking..."):
                        try:
                            result = st.session_state.orchestrator.answer(question)
                            
                            badge = get_method_badge(result.get("method", ""))
                            st.markdown(f'<span class="method-badge">{badge}</span>', unsafe_allow_html=True)
                            
                            answer_text = result.get("answer", "I couldn't find an answer.")
                            st.markdown(answer_text)
                            
                            sources_text = format_sources_for_display(result.get("sources", []))
                            if sources_text:
                                st.markdown(sources_text)
                            
                            # Generate TTS audio for the answer
                            audio_path = None
                            try:
                                short_answer = answer_text[:500]  # Limit TTS length
                                audio_path = st.session_state.voice_agent.text_to_speech(short_answer)
                                st.audio(audio_path, format="audio/mp3")
                            except Exception as tts_err:
                                st.caption(f"(TTS unavailable: {tts_err})")
                            
                            # Save to history
                            st.session_state.chat_history.append({
                                "role": "assistant",
                                "content": answer_text,
                                "method": result.get("method", ""),
                                "sources_text": sources_text,
                                "audio_path": audio_path
                            })
                        
                        except Exception as e:
                            st.error(f"Error: {e}")
    
    with tab2:
        st.markdown("### 🎙️ Voice Mode")
        st.markdown("Speak your question, get a spoken answer back.")
        
        col1, col2 = st.columns(2)
        
        with col1:
            duration = st.slider("Recording duration (seconds)", 3, 10, 5)
            
            if st.button("🔴 Start Recording", use_container_width=True):
                if not st.session_state.voice_agent:
                    st.error("Enter API key first")
                else:
                    with st.spinner(f"🎤 Recording for {duration}s... Speak now!"):
                        try:
                            transcribed = st.session_state.voice_agent.record_and_transcribe(duration)
                            st.session_state.voice_transcription = transcribed
                            st.success(f"✅ You said: *\"{transcribed}\"*")
                        except Exception as e:
                            st.error(f"Recording error: {e}\n\nMake sure your microphone is connected.")
        
        with col2:
            if st.session_state.get("voice_transcription"):
                st.markdown(f"**Transcribed:** _{st.session_state.voice_transcription}_")
                
                if st.button("🚀 Get Answer", use_container_width=True):
                    with st.spinner("Processing..."):
                        result = st.session_state.orchestrator.answer(
                            st.session_state.voice_transcription
                        )
                        
                        answer_text = result.get("answer", "No answer found.")
                        st.markdown("**Answer:**")
                        st.markdown(answer_text)
                        
                        # Speak the answer
                        try:
                            audio_path = st.session_state.voice_agent.text_to_speech(answer_text[:500])
                            st.audio(audio_path, format="audio/mp3")
                        except Exception as e:
                            st.warning(f"TTS error: {e}")