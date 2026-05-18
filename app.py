import os
import requests
import streamlit as st
from dotenv import load_dotenv

from ui.styles import inject_css
from ui.sidebar import render_sidebar
from ui.chat import render_chat

load_dotenv()

st.set_page_config(
    page_title="MindVault — Knowledge Base Chatbot",
    page_icon="📚",
    layout="wide",
    initial_sidebar_state="expanded",
)

inject_css()

# ── Session state defaults ────────────────────────────────────────
if "messages" not in st.session_state:
    st.session_state.messages = []
if "chain" not in st.session_state:
    st.session_state.chain = None
if "collection_name" not in st.session_state:
    st.session_state.collection_name = os.getenv("DEFAULT_COLLECTION", "my_knowledge_base")


# ── Ollama health check ───────────────────────────────────────────
def _ollama_ok() -> bool:
    try:
        r = requests.get(
            os.getenv("OLLAMA_BASE_URL", "http://localhost:11434"),
            timeout=2,
        )
        return r.status_code == 200
    except Exception:
        return False


# ── Sidebar ───────────────────────────────────────────────────────
settings = render_sidebar()

# ── Main header ───────────────────────────────────────────────────
st.title("MindVault")
st.caption(
    f"Collection: `{st.session_state.collection_name}` | "
    f"Model: `{settings['model']}` | "
    f"Top-K: `{settings['retrieval_k']}`"
)

# ── Ollama status banner ──────────────────────────────────────────
if not _ollama_ok():
    st.warning(
        "Ollama is not reachable. Start it with:\n\n"
        "```bash\nsudo systemctl start ollama\n```",
        icon="⚠️",
    )

st.divider()

# ── Chat ──────────────────────────────────────────────────────────
render_chat()
