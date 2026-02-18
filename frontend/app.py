import time
import logging
from pathlib import Path

import requests
import streamlit as st

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("university_faq.ui")

API_BASE = "http://localhost:8000"
CSS_PATH = Path(__file__).parent / "styles.css"

SUGGESTED_QUESTIONS = [
    "What is the attendance policy?",
    "How do I apply for hostel accommodation?",
    "What are the exam regulations?",
    "What programs does Karunya offer?",
    "What documents are needed for admission?",
    "What is the library book issue policy?",
]

SVG_LOGO = """
<svg width="48" height="48" viewBox="0 0 48 48" xmlns="http://www.w3.org/2000/svg">
  <defs>
    <linearGradient id="grad" x1="0%" y1="0%" x2="100%" y2="100%">
      <stop offset="0%" style="stop-color:#6C63FF;stop-opacity:1" />
      <stop offset="100%" style="stop-color:#3B82F6;stop-opacity:1" />
    </linearGradient>
  </defs>
  <rect rx="12" width="48" height="48" fill="url(#grad)"/>
  <text x="24" y="32" text-anchor="middle" fill="white" font-size="24" font-weight="bold" font-family="Arial">U</text>
</svg>
"""


def load_css() -> None:
    """Inject custom CSS into Streamlit."""
    if CSS_PATH.exists():
        st.markdown(f"<style>{CSS_PATH.read_text()}</style>", unsafe_allow_html=True)


def render_header() -> None:
    """Render premium header with SVG logo and tagline."""
    st.markdown(
        f"""
        <div class="header-container">
            <div class="header-logo">{SVG_LOGO}</div>
            <div class="header-text">
                <h1 class="header-title">University FAQ Assistant</h1>
                <p class="header-tagline">Smart Campus AI — Powered by ScaleDown Compression</p>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_metrics() -> None:
    """Render compression and performance metrics."""
    if "upload_stats" not in st.session_state:
        return
    stats = st.session_state.upload_stats
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.markdown(
            f"""<div class="metric-card">
                <div class="metric-value">{stats['compression_ratio']:.1f}%</div>
                <div class="metric-label">Compression</div>
            </div>""",
            unsafe_allow_html=True,
        )
    with col2:
        st.markdown(
            f"""<div class="metric-card">
                <div class="metric-value">{stats['original_length']:,}</div>
                <div class="metric-label">Original Chars</div>
            </div>""",
            unsafe_allow_html=True,
        )
    with col3:
        st.markdown(
            f"""<div class="metric-card">
                <div class="metric-value">{stats['compressed_length']:,}</div>
                <div class="metric-label">Compressed</div>
            </div>""",
            unsafe_allow_html=True,
        )
    with col4:
        st.markdown(
            f"""<div class="metric-card">
                <div class="metric-value">{stats['processing_time_ms']:.0f}ms</div>
                <div class="metric-label">Process Time</div>
            </div>""",
            unsafe_allow_html=True,
        )


def init_default_session() -> None:
    """Fetch the preloaded Karunya University session from backend."""
    if "session_id" in st.session_state:
        return
    try:
        response = requests.get(f"{API_BASE}/default-session", timeout=10)
        if response.status_code == 200:
            data = response.json()
            st.session_state.session_id = data["session_id"]
            st.session_state.upload_stats = data
            st.session_state.messages = []
    except Exception:
        pass


def render_sidebar() -> None:
    """Render sidebar with settings and session info."""
    with st.sidebar:
        st.markdown("### ⚙️ Settings")

        if "dark_mode" not in st.session_state:
            st.session_state.dark_mode = True

        dark_mode = st.toggle("Dark Mode", value=st.session_state.dark_mode)
        if dark_mode != st.session_state.dark_mode:
            st.session_state.dark_mode = dark_mode
            st.rerun()

        st.markdown("---")
        st.markdown("### 🎓 Karunya University (KITS)")
        st.markdown(
            "Policy data is **preloaded** and indexed automatically. "
            "Ask any question about admissions, policies, courses, or campus life."
        )

        if "session_id" in st.session_state:
            st.markdown("---")
            st.success(f"Session: `{st.session_state.session_id}`")
            if st.button("🔄 Clear Chat History", use_container_width=True):
                st.session_state.messages = []
                st.toast("Chat cleared.", icon="🗑️")
                st.rerun()
        else:
            st.warning("Connecting to backend...")

        st.markdown("---")
        st.markdown(
            """<div style="text-align:center;opacity:0.5;font-size:12px;">
                Built by <b>JOSHUA ISRAEL</b>
            </div>""",
            unsafe_allow_html=True,
        )


def ask_question(question: str) -> dict:
    """Send question to backend and return answer."""
    try:
        response = requests.post(
            f"{API_BASE}/ask",
            json={
                "session_id": st.session_state.session_id,
                "question": question,
            },
            timeout=30,
        )
        if response.status_code == 200:
            return response.json()
        return {"answer": f"Error: {response.json().get('detail', 'Unknown')}", "sources": [], "confidence": 0, "response_time_ms": 0}
    except requests.exceptions.ConnectionError:
        return {"answer": "Cannot reach the API server. Please ensure the backend is running.", "sources": [], "confidence": 0, "response_time_ms": 0}
    except Exception as exc:
        return {"answer": f"Error: {exc}", "sources": [], "confidence": 0, "response_time_ms": 0}


def render_chat() -> None:
    """Render the ChatGPT-style chat interface."""
    if "messages" not in st.session_state:
        st.session_state.messages = []

    if "session_id" not in st.session_state:
        st.markdown(
            """<div class="empty-state">
                <h3>👋 Welcome to Karunya University FAQ</h3>
                <p>Please ensure the backend server is running on port 8000, then refresh this page.</p>
            </div>""",
            unsafe_allow_html=True,
        )
        return

    chat_container = st.container()
    with chat_container:
        for msg in st.session_state.messages:
            with st.chat_message(msg["role"]):
                st.markdown(msg["content"])
                if msg.get("meta"):
                    meta = msg["meta"]
                    st.caption(
                        f"⏱️ {meta.get('response_time_ms', 0):.0f}ms · "
                        f"🎯 {meta.get('confidence', 0):.0%} confidence"
                    )

    if not st.session_state.messages:
        render_suggested_questions()

    handle_chat_input()


def render_suggested_questions() -> None:
    """Render clickable suggested FAQ buttons."""
    st.markdown("#### 💡 Suggested Questions")
    cols = st.columns(3)
    for i, question in enumerate(SUGGESTED_QUESTIONS):
        with cols[i % 3]:
            if st.button(question, key=f"suggest_{i}", use_container_width=True):
                process_question(question)
                st.rerun()


def handle_chat_input() -> None:
    """Handle the floating chat input bar."""
    if prompt := st.chat_input("Ask anything about the university..."):
        process_question(prompt)
        st.rerun()


def process_question(question: str) -> None:
    """Process a user question: add to chat, call API, display answer."""
    st.session_state.messages.append({"role": "user", "content": question})

    result = ask_question(question)

    meta = {
        "response_time_ms": result.get("response_time_ms", 0),
        "confidence": result.get("confidence", 0),
    }

    st.session_state.messages.append({
        "role": "assistant",
        "content": result["answer"],
        "meta": meta,
    })


def render_footer() -> None:
    """Render professional footer."""
    st.markdown(
        """<div class="footer">
            <p>University FAQ Assistant v1.0 · Built with ❤️ by <b>JOSHUA ISRAEL</b></p>
            <p>Powered by FastAPI · FAISS · Sentence-Transformers · ScaleDown AI</p>
        </div>""",
        unsafe_allow_html=True,
    )


def main() -> None:
    """Application entrypoint."""
    st.set_page_config(
        page_title="University FAQ Assistant",
        page_icon="🎓",
        layout="wide",
        initial_sidebar_state="expanded",
    )

    load_css()

    if st.session_state.get("dark_mode", True):
        st.markdown('<div class="dark-mode">', unsafe_allow_html=True)

    render_header()
    init_default_session()
    render_metrics()
    render_sidebar()
    render_chat()
    render_footer()

    if st.session_state.get("dark_mode", True):
        st.markdown("</div>", unsafe_allow_html=True)


if __name__ == "__main__":
    main()
