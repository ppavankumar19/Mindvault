import os
import uuid
from pathlib import Path
from langchain_community.document_loaders import (
    PyPDFLoader,
    TextLoader,
    Docx2txtLoader,
    UnstructuredMarkdownLoader,
    UnstructuredEPubLoader,
)
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.schema import Document


SUPPORTED_EXTENSIONS = {
    ".pdf": PyPDFLoader,
    ".txt": TextLoader,
    ".md": UnstructuredMarkdownLoader,
    ".docx": Docx2txtLoader,
    ".epub": UnstructuredEPubLoader,
}


def load_document(file_path: str) -> list[Document]:
    """Load a file and return raw Document objects."""
    ext = Path(file_path).suffix.lower()
    loader_class = SUPPORTED_EXTENSIONS.get(ext)

    if not loader_class:
        raise ValueError(f"Unsupported file type: {ext}")

    # TextLoader needs explicit encoding to handle non-UTF8 files gracefully
    if loader_class is TextLoader:
        loader = TextLoader(file_path, encoding="utf-8", autodetect_encoding=True)
    else:
        loader = loader_class(file_path)

    docs = loader.load()

    # Guard: skip files that produce no text
    docs = [d for d in docs if d.page_content and d.page_content.strip()]
    if not docs:
        raise ValueError(f"No text could be extracted from: {Path(file_path).name}")

    return docs


def split_documents(
    documents: list[Document],
    chunk_size: int = 800,
    chunk_overlap: int = 150,
    doc_id: str = None,
) -> list[Document]:
    """Split documents into chunks and attach metadata."""
    if doc_id is None:
        doc_id = str(uuid.uuid4())

    splitter = RecursiveCharacterTextSplitter(
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap,
        separators=["\n\n", "\n", ". ", " ", ""],
    )

    chunks = splitter.split_documents(documents)

    for i, chunk in enumerate(chunks):
        chunk.metadata["doc_id"] = doc_id
        chunk.metadata["chunk_index"] = i

    return chunks


def load_and_split(
    file_path: str,
    chunk_size: int = 800,
    chunk_overlap: int = 150,
) -> tuple[list[Document], str]:
    """
    Full pipeline: load file, split into chunks.
    Returns (chunks, doc_id).
    """
    doc_id = str(uuid.uuid4())
    raw_docs = load_document(file_path)
    chunks = split_documents(raw_docs, chunk_size, chunk_overlap, doc_id)
    return chunks, doc_id


def load_folder(folder_path: str, **kwargs) -> list[tuple[list[Document], str]]:
    """Load all supported files from a folder recursively."""
    results = []
    for path in Path(folder_path).rglob("*"):
        if path.suffix.lower() in SUPPORTED_EXTENSIONS:
            try:
                chunks, doc_id = load_and_split(str(path), **kwargs)
                results.append((chunks, doc_id))
                print(f"Loaded: {path.name} ({len(chunks)} chunks)")
            except Exception as e:
                print(f"Failed: {path.name} — {e}")
    return results
