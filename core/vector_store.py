import os
from langchain_community.vectorstores import Chroma
from langchain.schema import Document


def get_or_create_collection(
    collection_name: str,
    embedding_model,
    persist_dir: str = None,
) -> Chroma:
    """Load existing or create a new ChromaDB collection."""
    persist_path = persist_dir or os.getenv("CHROMA_PERSIST_DIR", "./data/chroma_db")

    return Chroma(
        collection_name=collection_name,
        embedding_function=embedding_model,
        persist_directory=persist_path,
    )


def add_documents(collection: Chroma, documents: list[Document]) -> None:
    """Add chunked documents to the vector store."""
    collection.add_documents(documents)


def delete_document(collection: Chroma, doc_id: str) -> None:
    """Remove all chunks belonging to a document."""
    collection._collection.delete(where={"doc_id": doc_id})


def list_documents(collection: Chroma) -> list[dict]:
    """Return unique document names and IDs in the collection."""
    results = collection._collection.get(include=["metadatas"])
    metadatas = results.get("metadatas") or []
    seen = {}
    for meta in metadatas:
        doc_id = meta.get("doc_id", "unknown")
        source = meta.get("source", "unknown")
        if doc_id not in seen:
            seen[doc_id] = {"doc_id": doc_id, "source": source}
    return list(seen.values())
