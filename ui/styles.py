CUSTOM_CSS = """
<style>
/* ── Global ──────────────────────────────────────── */
html, body, [class*="css"] {
    font-family: 'Inter', 'Segoe UI', sans-serif;
}

/* ── Sidebar ─────────────────────────────────────── */
[data-testid="stSidebar"] {
    min-width: 280px;
    max-width: 340px;
    background-color: #f8f9fa;
    padding: 1rem 0.75rem;
}

[data-testid="stSidebar"] h1 {
    font-size: 1.2rem;
    font-weight: 700;
    margin-bottom: 0.5rem;
}

[data-testid="stSidebar"] .stButton > button {
    width: 100%;
    border-radius: 8px;
    font-size: 0.875rem;
    padding: 0.5rem 0.75rem;
    transition: background 0.2s;
}

/* ── Main area ───────────────────────────────────── */
.main .block-container {
    max-width: 860px;
    padding: 1.5rem 1rem 5rem 1rem;
    margin: 0 auto;
}

/* ── Chat messages ───────────────────────────────── */
[data-testid="stChatMessage"] {
    border-radius: 12px;
    padding: 0.75rem 1rem;
    margin-bottom: 0.5rem;
    max-width: 100%;
    word-wrap: break-word;
}

/* ── Source cards ────────────────────────────────── */
.source-card {
    background: #f0f4ff;
    border-left: 3px solid #4c6ef5;
    border-radius: 6px;
    padding: 0.6rem 0.8rem;
    margin-bottom: 0.5rem;
    font-size: 0.85rem;
}

.source-card strong {
    color: #2c3e50;
}

/* ── Status banner ───────────────────────────────── */
.status-ok {
    background: #d4edda;
    color: #155724;
    border-radius: 6px;
    padding: 0.4rem 0.75rem;
    font-size: 0.82rem;
    margin-bottom: 0.5rem;
}

.status-err {
    background: #f8d7da;
    color: #721c24;
    border-radius: 6px;
    padding: 0.4rem 0.75rem;
    font-size: 0.82rem;
    margin-bottom: 0.5rem;
}

/* ── Doc list items ──────────────────────────────── */
.doc-item {
    display: flex;
    align-items: center;
    justify-content: space-between;
    background: #fff;
    border: 1px solid #dee2e6;
    border-radius: 6px;
    padding: 0.35rem 0.6rem;
    margin-bottom: 0.3rem;
    font-size: 0.82rem;
    word-break: break-word;
}

/* ── Responsive: small screens ───────────────────── */
@media (max-width: 768px) {
    [data-testid="stSidebar"] {
        min-width: 100%;
        max-width: 100%;
    }

    .main .block-container {
        padding: 1rem 0.5rem 4rem 0.5rem;
    }

    [data-testid="stChatMessage"] {
        padding: 0.5rem 0.6rem;
    }
}
</style>
"""


def inject_css():
    """Call this at the top of app.py to apply custom styles."""
    import streamlit as st
    st.markdown(CUSTOM_CSS, unsafe_allow_html=True)
