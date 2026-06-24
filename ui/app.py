import streamlit as st
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils.helpers import load_api_key, save_uploaded_file, format_sources_for_display, get_method_badge
from core.ocr import extract_text_from_pdf
from core.embeddings import chunk_text
from core.vectorstore import DocumentVectorStore
from agents.orchestrator import ProcurementOrchestrator
from agents.voice_agent import VoiceAgent

st.set_page_config(
    page_title="ProcureAI",
    page_icon="📋",
    layout="wide",
    initial_sidebar_state="collapsed"
)

st.markdown("""
<style>
    .main-header {
        background: linear-gradient(135deg, #1a1a2e 0%, #0f3460 100%);
        padding: 1.5rem 2rem;
        border-radius: 12px;
        margin-bottom: 1.5rem;
        color: white;
        text-align: center;
    }
    .method-badge {
        display: inline-block;
        background: #e0e7ff;
        color: #4f46e5;
        padding: 0.2rem 0.7rem;
        border-radius: 20px;
        font-size: 0.8rem;
        margin-bottom: 0.5rem;
    }
    .doc-pill {
        display: inline-block;
        background: #dcfce7;
        color: #166534;
        padding: 0.2rem 0.6rem;
        border-radius: 12px;
        font-size: 0.78rem;
        margin: 0.1rem;
    }
</style>
""", unsafe_allow_html=True)

# Session state
for key, val in {
    "vectorstore": None, "orchestrator": None, "voice_agent": None,
    "chat_history": [], "api_key": None, "docs_loaded": []
}.items():
    if key not in st.session_state:
        st.session_state[key] = val


def initialize_agents(api_key):
    vs = DocumentVectorStore(persist_directory="./data/vectorstore")
    st.session_state.vectorstore = vs
    st.session_state.orchestrator = ProcurementOrchestrator(api_key, vs)
    st.session_state.voice_agent = VoiceAgent(api_key)
    st.session_state.api_key = api_key


def process_pdf(pdf_path, doc_name, api_key):
    import time
    from google import genai as g

    with st.spinner(f"🔍 OCR — reading {doc_name}..."):
        text = extract_text_from_pdf(pdf_path, api_key)
    with st.spinner("✂️ Chunking..."):
        chunks = chunk_text(text, chunk_size=600, overlap=50)

    st.write(f"🧠 Embedding {len(chunks)} chunks (~{len(chunks) * 2}s)...")
    progress = st.progress(0)
    c = g.Client(api_key=api_key)

    for i, chunk in enumerate(chunks):
        result = c.models.embed_content(
            model="models/gemini-embedding-001",
            contents=chunk["text"],
            config={"output_dimensionality": 768}
        )
        embedding = list(result.embeddings[0].values)
        st.session_state.vectorstore.add_single_chunk(
            text=chunk["text"],
            embedding=embedding,
            doc_name=doc_name,
            chunk_id=chunk["chunk_id"],
            start_char=chunk["start_char"],
            end_char=chunk["end_char"]
        )
        del embedding, result
        progress.progress((i + 1) / len(chunks))
        time.sleep(0.3)

    progress.empty()
    return len(chunks)

# ── Header ──
st.markdown("""
<div class="main-header">
    <h2 style="margin:0">📋 ProcureAI</h2>
    <p style="margin:0.3rem 0 0; opacity:0.8">Intelligent Procurement Document Agent</p>
</div>
""", unsafe_allow_html=True)

# ── API Key (top, compact) ──
if not st.session_state.api_key:
    try:
        initialize_agents(load_api_key())
    except:
        pass

if not st.session_state.api_key:
    key_input = st.text_input("🔑 Enter Gemini API Key to get started", type="password")
    if key_input:
        initialize_agents(key_input)
        st.rerun()
    st.stop()

# ── Document upload bar (above chat) ──
with st.container():
    col1, col2 = st.columns([3, 1])
    with col1:
        uploaded = st.file_uploader(
            "📎 Upload PDF to chat with it",
            type=["pdf"],
            label_visibility="collapsed"
        )
    with col2:
        if uploaded and uploaded.name not in st.session_state.docs_loaded:
            if st.button("⚡ Process PDF", use_container_width=True):
                path = save_uploaded_file(uploaded)
                n = process_pdf(path, uploaded.name, st.session_state.api_key)
                st.session_state.docs_loaded.append(uploaded.name)
                st.success(f"✅ {uploaded.name} ready — {n} chunks indexed")
                st.rerun()

# Show loaded docs as pills
if st.session_state.docs_loaded:
    pills = " ".join([f'<span class="doc-pill">📄 {d}</span>' for d in st.session_state.docs_loaded])
    st.markdown(f"**Indexed:** {pills}", unsafe_allow_html=True)

st.divider()

# ── Chat history ──
for msg in st.session_state.chat_history:
    with st.chat_message(msg["role"]):
        if msg["role"] == "assistant" and msg.get("method"):
            st.markdown(f'<span class="method-badge">{get_method_badge(msg["method"])}</span>', unsafe_allow_html=True)
        st.markdown(msg["content"])
        if msg.get("sources_text"):
            st.markdown(msg["sources_text"])
        if msg.get("audio_path") and os.path.exists(msg["audio_path"]):
            st.audio(msg["audio_path"], format="audio/mp3")

# ── Chat input ──
question = st.chat_input("Ask anything about your documents...")

if question:
    st.session_state.chat_history.append({"role": "user", "content": question})
    with st.chat_message("user"):
        st.markdown(question)

    with st.chat_message("assistant"):
        with st.spinner("Thinking..."):
            try:
                result = st.session_state.orchestrator.answer(question)
                answer = result.get("answer", "I couldn't find an answer.")
                method = result.get("method", "")
                sources_text = format_sources_for_display(result.get("sources", []))

                if method:
                    st.markdown(f'<span class="method-badge">{get_method_badge(method)}</span>', unsafe_allow_html=True)
                st.markdown(answer)
                if sources_text:
                    st.markdown(sources_text)

                # TTS
                audio_path = None
                try:
                    audio_path = st.session_state.voice_agent.text_to_speech(answer[:500])
                    st.audio(audio_path, format="audio/mp3")
                except:
                    pass

                st.session_state.chat_history.append({
                    "role": "assistant",
                    "content": answer,
                    "method": method,
                    "sources_text": sources_text,
                    "audio_path": audio_path
                })
            except Exception as e:
                st.error(f"Error: {e}")