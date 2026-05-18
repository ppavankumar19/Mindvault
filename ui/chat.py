import streamlit as st
from core.chain import run_chain


def render_chat():
    """Render the main chat interface."""
    if st.session_state.chain is None:
        st.info(
            "**Getting started:**\n\n"
            "1. Upload one or more documents in the sidebar\n"
            "2. Click **Ingest Documents**\n"
            "3. Start asking questions!"
        )
        return

    # ── Chat history ────────────────────────────────────────────────
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])
            if message.get("sources"):
                _render_sources(message["sources"])

    # ── Input ────────────────────────────────────────────────────────
    if question := st.chat_input("Ask a question about your documents..."):
        st.session_state.messages.append({"role": "user", "content": question})
        with st.chat_message("user"):
            st.markdown(question)

        with st.chat_message("assistant"):
            with st.spinner("Thinking..."):
                try:
                    result = run_chain(st.session_state.chain, question)
                    answer = result["answer"]
                    sources = result["sources"]

                    st.markdown(answer)
                    _render_sources(sources)

                    st.session_state.messages.append({
                        "role": "assistant",
                        "content": answer,
                        "sources": sources,
                    })

                except Exception as e:
                    err = str(e)
                    if "connection" in err.lower() or "refused" in err.lower():
                        st.error(
                            "Cannot reach Ollama. Make sure it is running:\n\n"
                            "```bash\nsudo systemctl start ollama\n```"
                        )
                    else:
                        st.error(f"Error: {err}")


def _render_sources(sources: list):
    if not sources:
        return
    with st.expander(f"Sources ({len(sources)})"):
        for src in sources:
            st.markdown(
                f"<div class='source-card'>"
                f"<strong>{src['doc_name']}</strong> — Page {src['page']}<br>"
                f"<small>{src['excerpt']}</small>"
                f"</div>",
                unsafe_allow_html=True,
            )
