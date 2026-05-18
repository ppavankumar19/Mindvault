import pytest
from core.embeddings import get_embedding_model
from core.vector_store import get_or_create_collection, add_documents
from core.ingestion import load_and_split
from core.llm import get_llm
from core.chain import build_rag_chain, run_chain
from pathlib import Path

FIXTURES = Path(__file__).parent / "fixtures"


@pytest.fixture(scope="module")
def rag_chain(tmp_path_factory):
    tmp_dir = str(tmp_path_factory.mktemp("chroma"))
    embed_model = get_embedding_model()
    collection = get_or_create_collection("test_col", embed_model, persist_dir=tmp_dir)
    chunks, _ = load_and_split(str(FIXTURES / "sample.txt"))
    add_documents(collection, chunks)
    llm = get_llm("llama3.2:3b")
    retriever = collection.as_retriever(search_kwargs={"k": 3})
    return build_rag_chain(llm, retriever)


def test_chain_returns_answer(rag_chain):
    result = run_chain(rag_chain, "What is this document about?")
    assert "answer" in result
    assert len(result["answer"]) > 0


def test_chain_returns_sources(rag_chain):
    result = run_chain(rag_chain, "Summarize the main topic.")
    assert "sources" in result
    assert isinstance(result["sources"], list)
