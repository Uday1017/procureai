import streamlit as st
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

st.set_page_config(
    page_title="ProcureAI",
    page_icon="data:image/svg+xml,<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 100 100'><rect width='100' height='100' rx='20' fill='%237C3AED'/><path d='M25 35h50M25 50h35M25 65h42' stroke='white' stroke-width='8' stroke-linecap='round'/></svg>",
    layout="wide",
    initial_sidebar_state="collapsed"
)

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@300;400;500;600;700&family=Inter:wght@300;400;500;600&family=JetBrains+Mono:wght@400;500&display=swap');

*, *::before, *::after { box-sizing: border-box; margin: 0; padding: 0; }

html, body, [data-testid="stAppViewContainer"] {
    background: #0A0A0F !important;
    color: #F8FAFC !important;
    font-family: 'Inter', sans-serif !important;
}
[data-testid="stAppViewContainer"] > .main { background: #0A0A0F !important; }
[data-testid="stHeader"] { background: transparent !important; }
[data-testid="stToolbar"] { display: none !important; }
.stDeployButton { display: none !important; }
#MainMenu { display: none !important; }
footer { display: none !important; }

::-webkit-scrollbar { width: 4px; }
::-webkit-scrollbar-track { background: #0A0A0F; }
::-webkit-scrollbar-thumb { background: #2D2D3F; border-radius: 2px; }

/* Header */
.procure-header {
    display: flex;
    align-items: center;
    justify-content: space-between;
    padding: 1rem 2rem;
    border-bottom: 1px solid #1E1E2E;
    background: #0A0A0F;
}
.procure-logo {
    display: flex;
    align-items: center;
    gap: 0.65rem;
}
.logo-mark {
    width: 30px; height: 30px;
    background: linear-gradient(135deg, #7C3AED, #4F46E5);
    border-radius: 7px;
    display: flex; align-items: center; justify-content: center;
}
.logo-text {
    font-family: 'Space Grotesk', sans-serif;
    font-weight: 700;
    font-size: 1.05rem;
    color: #F8FAFC;
    letter-spacing: -0.02em;
}
.logo-badge {
    font-family: 'JetBrains Mono', monospace;
    font-size: 0.6rem;
    color: #7C3AED;
    background: #1A1030;
    border: 1px solid #2D1B69;
    padding: 0.12rem 0.45rem;
    border-radius: 4px;
    letter-spacing: 0.08em;
}
.header-right {
    display: flex;
    align-items: center;
    gap: 0.5rem;
    font-size: 0.72rem;
    color: #4B5563;
    font-family: 'JetBrains Mono', monospace;
}
.status-dot {
    width: 6px; height: 6px;
    background: #10B981;
    border-radius: 50%;
    animation: pulse-dot 2s ease-in-out infinite;
}
@keyframes pulse-dot {
    0%, 100% { opacity: 1; }
    50% { opacity: 0.4; }
}

/* Panel label */
.panel-label {
    font-family: 'JetBrains Mono', monospace;
    font-size: 0.62rem;
    color: #374151;
    text-transform: uppercase;
    letter-spacing: 0.14em;
    margin-bottom: 0.65rem;
}

/* Doc item */
.doc-item {
    display: flex;
    align-items: center;
    gap: 0.55rem;
    padding: 0.55rem 0.7rem;
    background: #111118;
    border: 1px solid #1E1E2E;
    border-radius: 8px;
    margin-bottom: 0.4rem;
}
.doc-icon-wrap {
    width: 26px; height: 26px;
    background: #1A1030;
    border-radius: 5px;
    display: flex; align-items: center; justify-content: center;
    flex-shrink: 0;
}
.doc-name {
    font-size: 0.72rem;
    color: #CBD5E1;
    font-family: 'JetBrains Mono', monospace;
    white-space: nowrap;
    overflow: hidden;
    text-overflow: ellipsis;
    flex: 1;
}
.doc-ok {
    width: 16px; height: 16px;
    background: #0D1F17;
    border-radius: 50%;
    display: flex; align-items: center; justify-content: center;
    flex-shrink: 0;
}

/* Divider */
hr { border: none; border-top: 1px solid #1E1E2E !important; margin: 1rem 0 !important; }

/* Empty state */
.empty-state {
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    padding: 5rem 2rem;
    text-align: center;
}
.empty-orb {
    width: 72px; height: 72px;
    background: radial-gradient(circle at 35% 35%, #7C3AED, #312E81);
    border-radius: 50%;
    margin-bottom: 1.5rem;
    box-shadow: 0 0 50px rgba(124,58,237,0.25);
    animation: breathe 3s ease-in-out infinite;
}
@keyframes breathe {
    0%, 100% { box-shadow: 0 0 30px rgba(124,58,237,0.2); transform: scale(1); }
    50% { box-shadow: 0 0 70px rgba(124,58,237,0.4); transform: scale(1.04); }
}
.empty-title {
    font-family: 'Space Grotesk', sans-serif;
    font-size: 1.35rem;
    font-weight: 700;
    color: #F8FAFC;
    margin-bottom: 0.5rem;
    letter-spacing: -0.02em;
}
.empty-sub {
    font-size: 0.82rem;
    color: #374151;
    line-height: 1.7;
    max-width: 320px;
}

/* Method tag */
.method-tag {
    display: inline-flex;
    align-items: center;
    gap: 0.3rem;
    font-family: 'JetBrains Mono', monospace;
    font-size: 0.62rem;
    color: #7C3AED;
    background: #1A1030;
    border: 1px solid #2D1B69;
    padding: 0.18rem 0.5rem;
    border-radius: 4px;
    margin-bottom: 0.5rem;
    letter-spacing: 0.04em;
    text-transform: uppercase;
}

/* Streamlit overrides */
[data-testid="stChatInput"] {
    background: #111118 !important;
    border: 1px solid #2D2D3F !important;
    border-radius: 10px !important;
}
[data-testid="stChatInput"]:focus-within {
    border-color: #7C3AED !important;
    box-shadow: 0 0 0 3px rgba(124,58,237,0.08) !important;
}
[data-testid="stChatInput"] button {
    background: linear-gradient(135deg, #7C3AED, #4F46E5) !important;
    border-radius: 7px !important;
    border: none !important;
}
[data-testid="stChatInput"] textarea {
    color: #F8FAFC !important;
    font-family: 'Inter', sans-serif !important;
    font-size: 0.875rem !important;
}

.stButton button {
    background: #111118 !important;
    border: 1px solid #1E1E2E !important;
    color: #64748B !important;
    border-radius: 8px !important;
    font-family: 'Inter', sans-serif !important;
    font-size: 0.78rem !important;
    font-weight: 500 !important;
    transition: all 0.15s !important;
    padding: 0.4rem 0.75rem !important;
}
.stButton button:hover {
    border-color: #7C3AED !important;
    color: #C4B5FD !important;
    background: #13101E !important;
}

.process-btn .stButton button {
    background: linear-gradient(135deg, #7C3AED, #4F46E5) !important;
    border: none !important;
    color: #fff !important;
    font-weight: 600 !important;
}
.process-btn .stButton button:hover {
    opacity: 0.9 !important;
    color: #fff !important;
    border: none !important;
}

.voice-btn .stButton button {
    background: #111118 !important;
    border: 1px solid #1E1E2E !important;
    color: #64748B !important;
    border-radius: 8px !important;
    width: 40px !important;
    height: 40px !important;
    padding: 0 !important;
    display: flex !important;
    align-items: center !important;
    justify-content: center !important;
}
.voice-btn .stButton button:hover {
    border-color: #10B981 !important;
    color: #10B981 !important;
    background: #0D1F17 !important;
}

[data-testid="stFileUploader"] {
    background: #111118 !important;
    border: 1.5px dashed #2D2D3F !important;
    border-radius: 10px !important;
    padding: 0.5rem !important;
}
[data-testid="stFileUploader"] section {
    border: none !important;
    background: transparent !important;
}
[data-testid="stFileUploader"] label { color: #4B5563 !important; font-size: 0.78rem !important; }

[data-testid="stChatMessage"] { background: transparent !important; border: none !important; }
[data-testid="stChatMessage"] [data-testid="stMarkdownContainer"] p { font-size: 0.875rem !important; line-height: 1.7 !important; color: #CBD5E1 !important; }

[data-testid="stSuccess"] {
    background: #0D1F17 !important;
    border: 1px solid #10B981 !important;
    border-radius: 8px !important;
    color: #10B981 !important;
    font-size: 0.8rem !important;
}

[data-testid="stTextInput"] input {
    background: #111118 !important;
    border: 1px solid #2D2D3F !important;
    border-radius: 8px !important;
    color: #F8FAFC !important;
    font-family: 'Inter', sans-serif !important;
    font-size: 0.875rem !important;
}

[data-testid="stProgressBar"] > div > div {
    background: linear-gradient(90deg, #7C3AED, #4F46E5) !important;
    border-radius: 4px !important;
}

[data-testid="stHorizontalBlock"] { gap: 0.75rem !important; }
</style>
""", unsafe_allow_html=True)

# SVG icons
ICON_DOC = '<svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="#7C3AED" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/><polyline points="14 2 14 8 20 8"/><line x1="16" y1="13" x2="8" y2="13"/><line x1="16" y1="17" x2="8" y2="17"/><polyline points="10 9 9 9 8 9"/></svg>'
ICON_CHECK = '<svg width="10" height="10" viewBox="0 0 24 24" fill="none" stroke="#10B981" stroke-width="3" stroke-linecap="round" stroke-linejoin="round"><polyline points="20 6 9 17 4 12"/></svg>'
ICON_MIC = '<svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M12 1a3 3 0 0 0-3 3v8a3 3 0 0 0 6 0V4a3 3 0 0 0-3-3z"/><path d="M19 10v2a7 7 0 0 1-14 0v-2"/><line x1="12" y1="19" x2="12" y2="23"/><line x1="8" y1="23" x2="16" y2="23"/></svg>'
ICON_LOGO = '<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="white" stroke-width="2.5" stroke-linecap="round"><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/><line x1="8" y1="12" x2="16" y2="12"/><line x1="8" y1="16" x2="13" y2="16"/></svg>'
ICON_BOLT = '<svg width="11" height="11" viewBox="0 0 24 24" fill="#7C3AED" stroke="none"><polygon points="13 2 3 14 12 14 11 22 21 10 12 10 13 2"/></svg>'
ICON_GLOBE = '<svg width="11" height="11" viewBox="0 0 24 24" fill="none" stroke="#7C3AED" stroke-width="2" stroke-linecap="round"><circle cx="12" cy="12" r="10"/><line x1="2" y1="12" x2="22" y2="12"/><path d="M12 2a15.3 15.3 0 0 1 4 10 15.3 15.3 0 0 1-4 10 15.3 15.3 0 0 1-4-10 15.3 15.3 0 0 1 4-10z"/></svg>'

# Header
st.markdown(f"""
<div class="procure-header">
    <div class="procure-logo">
        <div class="logo-mark">{ICON_LOGO}</div>
        <span class="logo-text">ProcureAI</span>
        <span class="logo-badge">BETA</span>
    </div>
    <div class="header-right">
        <div class="status-dot"></div>
        gemini-2.5-flash &nbsp;·&nbsp; live
    </div>
</div>
""", unsafe_allow_html=True)

# Imports
try:
    from utils.helpers import load_api_key, save_uploaded_file, format_sources_for_display, get_method_badge
    from core.ocr import extract_text_from_pdf
    from core.embeddings import chunk_text
    from core.vectorstore import DocumentVectorStore
    from agents.orchestrator import ProcurementOrchestrator
    from agents.voice_agent import VoiceAgent
except ImportError as e:
    st.error(f"Import error: {e}")
    st.stop()

# Session state
for key, val in {
    "vectorstore": None, "orchestrator": None, "voice_agent": None,
    "chat_history": [], "api_key": None, "docs_loaded": [], "voice_question": None
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
    with st.spinner(f"Running OCR on {doc_name}..."):
        text = extract_text_from_pdf(pdf_path, api_key)
    with st.spinner("Splitting into chunks..."):
        chunks = chunk_text(text, chunk_size=600, overlap=50)
    prog = st.progress(0, text=f"Embedding chunk 1 of {len(chunks)}...")
    from google import genai as g
    import time
    c = g.Client(api_key=api_key)
    for i, chunk in enumerate(chunks):
        result = c.models.embed_content(
            model="models/gemini-embedding-001",
            contents=chunk["text"],
            config={"output_dimensionality": 768}
        )
        embedding = result.embeddings[0].values
        st.session_state.vectorstore.add_single_chunk(
            text=chunk["text"], embedding=embedding, doc_name=doc_name,
            chunk_id=chunk["chunk_id"], start_char=chunk["start_char"], end_char=chunk["end_char"]
        )
        del embedding, result
        prog.progress((i + 1) / len(chunks), text=f"Embedding chunk {i+1} of {len(chunks)}...")
        time.sleep(0.3)
    prog.empty()
    return len(chunks)


# Auto-load key
if not st.session_state.api_key:
    try:
        initialize_agents(load_api_key())
    except:
        pass

# API key gate
if not st.session_state.api_key:
    st.markdown("<br><br>", unsafe_allow_html=True)
    _, col, _ = st.columns([1, 2, 1])
    with col:
        st.markdown("""
        <div style="text-align:center;margin-bottom:1.5rem;">
            <div style="font-family:'Space Grotesk',sans-serif;font-size:1.4rem;font-weight:700;color:#F8FAFC;margin-bottom:0.4rem;letter-spacing:-0.02em;">
                Connect your API key
            </div>
            <div style="font-size:0.8rem;color:#374151;">
                Free key at <a href="https://aistudio.google.com" target="_blank" style="color:#7C3AED;text-decoration:none;">aistudio.google.com</a>
            </div>
        </div>
        """, unsafe_allow_html=True)
        key_input = st.text_input("API Key", type="password", placeholder="AIza...", label_visibility="collapsed")
        if key_input:
            initialize_agents(key_input)
            st.rerun()
    st.stop()

# Main layout
left, right = st.columns([1, 3.2])

# LEFT panel
with left:
    st.markdown('<div class="panel-label">Documents</div>', unsafe_allow_html=True)

    uploaded = st.file_uploader("Upload PDF", type=["pdf"], label_visibility="collapsed")

    if uploaded and uploaded.name not in st.session_state.docs_loaded:
        st.markdown('<div class="process-btn">', unsafe_allow_html=True)
        if st.button("Process document", use_container_width=True):
            path = save_uploaded_file(uploaded)
            n = process_pdf(path, uploaded.name, st.session_state.api_key)
            st.session_state.docs_loaded.append(uploaded.name)
            st.success(f"Indexed — {n} chunks stored")
            st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)

    if st.session_state.docs_loaded:
        st.markdown("<hr>", unsafe_allow_html=True)
        st.markdown('<div class="panel-label">Indexed</div>', unsafe_allow_html=True)
        for doc in st.session_state.docs_loaded:
            short = doc[:22] + "…" if len(doc) > 24 else doc
            st.markdown(f"""
            <div class="doc-item">
                <div class="doc-icon-wrap">{ICON_DOC}</div>
                <span class="doc-name">{short}</span>
                <div class="doc-ok">{ICON_CHECK}</div>
            </div>
            """, unsafe_allow_html=True)

        if st.button("Clear documents", use_container_width=True):
            st.session_state.vectorstore.clear_all()
            st.session_state.docs_loaded = []
            st.session_state.chat_history = []
            st.rerun()

    st.markdown("<hr>", unsafe_allow_html=True)
    st.markdown('<div class="panel-label">Quick ask</div>', unsafe_allow_html=True)

    for q in ["Total invoice amount?", "Payment terms?", "Delivery deadline?",
              "Vendor details?", "Current market price?"]:
        if st.button(q, key=f"q_{q}", use_container_width=True):
            st.session_state.voice_question = q

# RIGHT: chat
with right:
    if not st.session_state.chat_history:
        st.markdown("""
        <div class="empty-state">
            <div class="empty-orb"></div>
            <div class="empty-title">Ready to analyse</div>
            <div class="empty-sub">Upload a procurement document on the left, then ask anything — or ask a general procurement question without uploading anything.</div>
        </div>
        """, unsafe_allow_html=True)
    else:
        for msg in st.session_state.chat_history:
            with st.chat_message(msg["role"]):
                if msg["role"] == "assistant" and msg.get("method"):
                    method = msg["method"]
                    icon = ICON_BOLT if "rag" in method else ICON_GLOBE
                    label = "from documents" if "rag" in method and "web" not in method else "web search" if "web" in method else "combined"
                    st.markdown(f'<div class="method-tag">{icon}&nbsp;{label}</div>', unsafe_allow_html=True)
                st.markdown(msg["content"])
                if msg.get("sources_text"):
                    st.markdown(msg["sources_text"])

    # Voice button + chat input
    vcol, _ = st.columns([1, 12])
    with vcol:
        st.markdown('<div class="voice-btn">', unsafe_allow_html=True)
        voice_btn = st.button(ICON_MIC, help="Click and speak for 5 seconds", use_container_width=True)
        st.markdown('</div>', unsafe_allow_html=True)

    if voice_btn:
        with st.spinner("Listening — speak now..."):
            try:
                transcribed = st.session_state.voice_agent.record_and_transcribe(5)
                st.session_state.voice_question = transcribed
                st.toast(f'Heard: "{transcribed}"')
            except Exception as e:
                st.error(f"Microphone error: {e}")

    voice_q = st.session_state.pop("voice_question", None)
    question = st.chat_input("Ask about your documents, or anything procurement related...") or voice_q

    if question:
        st.session_state.chat_history.append({"role": "user", "content": question})
        with st.chat_message("user"):
            st.markdown(question)

        with st.chat_message("assistant"):
            with st.spinner(""):
                try:
                    result = st.session_state.orchestrator.answer(question)
                    answer = result.get("answer", "No answer found.")
                    method = result.get("method", "")
                    sources_text = format_sources_for_display(result.get("sources", []))

                    if method:
                        icon = ICON_BOLT if "rag" in method and "web" not in method else ICON_GLOBE
                        label = "from documents" if "rag" in method and "web" not in method else "web search" if method == "web_search" or method == "web_search_fallback" else "combined"
                        st.markdown(f'<div class="method-tag">{icon}&nbsp;{label}</div>', unsafe_allow_html=True)

                    st.markdown(answer)
                    if sources_text:
                        st.markdown(sources_text)

                    st.session_state.chat_history.append({
                        "role": "assistant", "content": answer,
                        "method": method, "sources_text": sources_text
                    })
                except Exception as e:
                    st.error(f"Error: {e}")