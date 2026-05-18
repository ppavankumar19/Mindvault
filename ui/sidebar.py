import streamlit as st
from core.embeddings import get_embedding_model
from core.vector_store import get_or_create_collection, list_documents, delete_document
from core.retriever import get_retriever
from core.llm import get_llm
from core.chain import build_rag_chain


AVAILABLE_MODELS = ["llama3.2:3b", "mistral:7b", "phi3:mini", "gemma2:2b", "llama3.1:8b"]


def render_sidebar() -> dict:
    """
    Render full sidebar. Returns current settings dict.
    """
    with st.sidebar:
        st.title("MindVault")
        st.caption("Your local AI knowledge base")
        st.divider()

        # ── Collection ──────────────────────────────────────
        st.subheader("Collection")
        collection_name = st.text_input(
            "Name",
            value=st.session_state.get("collection_name", "my_knowledge_base"),
            key="collection_input",
        )

        # ── Model ───────────────────────────────────────────
        st.subheader("Model")
        model = st.selectbox("LLM", AVAILABLE_MODELS, index=0)

        # ── RAG Tuning ──────────────────────────────────────
        with st.expander("RAG Settings"):
            chunk_size = st.slider("Chunk Size (chars)", 300, 2000, 800, step=100)
            chunk_overlap = st.slider("Chunk Overlap", 0, 400, 150, step=50)
            retrieval_k = st.slider("Top-K Chunks", 1, 10, 5)

        st.divider()

        # ── Upload ──────────────────────────────────────────
        st.subheader("Upload Documents")
        uploaded_files = st.file_uploader(
            "PDF, TXT, MD, DOCX",
            type=["pdf", "txt", "md", "docx"],
            accept_multiple_files=True,
            label_visibility="collapsed",
        )

        if uploaded_files and st.button("Ingest Documents", type="primary"):
            _ingest(uploaded_files, collection_name, model, chunk_size, chunk_overlap, retrieval_k)

        st.divider()

        # ── Load collection ─────────────────────────────────
        col1, col2 = st.columns(2)
        with col1:
            if st.button("Load / Reload", use_container_width=True):
                _load_collection(collection_name, model, retrieval_k)
        with col2:
            if st.button("Clear Chat", use_container_width=True):
                st.session_state.messages = []
                if st.session_state.chain:
                    st.session_state.chain.memory.clear()
                st.rerun()

        # ── Ingested docs list ──────────────────────────────
        _render_doc_list(collection_name)

    return {
        "collection_name": collection_name,
        "model": model,
        "chunk_size": chunk_size,
        "chunk_overlap": chunk_overlap,
        "retrieval_k": retrieval_k,
    }


def _ingest(uploaded_files, collection_name, model, chunk_size, chunk_overlap, retrieval_k):
    from core.ingestion import load_and_split
    from core.vector_store import add_documents
    import os, tempfile

    embed_model = get_embedding_model()
    collection = get_or_create_collection(collection_name, embed_model)
    progress = st.progress(0)
    total = len(uploaded_files)

    for i, uploaded_file in enumerate(uploaded_files):
        with st.spinner(f"Processing {uploaded_file.name}..."):
            suffix = os.path.splitext(uploaded_file.name)[1]
            with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
                tmp.write(uploaded_file.read())
                tmp_path = tmp.name

            try:
                chunks, doc_id = load_and_split(tmp_path, chunk_size, chunk_overlap)
                for chunk in chunks:
                    chunk.metadata["source"] = uploaded_file.name
                add_documents(collection, chunks)
                st.success(f"{uploaded_file.name} — {len(chunks)} chunks")
            except Exception as e:
                st.error(f"{uploaded_file.name}: {e}")
            finally:
                os.unlink(tmp_path)

        progress.progress((i + 1) / total)

    progress.empty()
    llm = get_llm(model)
    retriever = get_retriever(collection, retrieval_k)
    st.session_state.chain = build_rag_chain(llm, retriever)
    st.session_state.collection_name = collection_name
    st.rerun()


def _load_collection(collection_name, model, retrieval_k):
    with st.spinner("Loading collection..."):
        embed_model = get_embedding_model()
        collection = get_or_create_collection(collection_name, embed_model)
        llm = get_llm(model)
        retriever = get_retriever(collection, retrieval_k)
        st.session_state.chain = build_rag_chain(llm, retriever)
        st.session_state.collection_name = collection_name
        docs = list_documents(collection)
        st.success(f"Loaded {len(docs)} document(s) in '{collection_name}'")
    st.rerun()


def _render_doc_list(collection_name: str):
    """Show ingested documents with delete buttons."""
    try:
        embed_model = get_embedding_model()
        collection = get_or_create_collection(collection_name, embed_model)
        docs = list_documents(collection)
    except Exception:
        return

    if not docs:
        return

    st.divider()
    st.subheader(f"Documents ({len(docs)})")

    for doc in docs:
        col1, col2 = st.columns([5, 1])
        with col1:
            name = doc["source"].split("/")[-1] if "/" in doc["source"] else doc["source"]
            st.markdown(
                f"<div class='doc-item'>📄 {name}</div>",
                unsafe_allow_html=True,
            )
        with col2:
            if st.button("✕", key=f"del_{doc['doc_id']}", help="Delete document"):
                try:
                    delete_document(collection, doc["doc_id"])
                    st.success("Deleted")
                    st.rerun()
                except Exception as e:
                    st.error(str(e))
