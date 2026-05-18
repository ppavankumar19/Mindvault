import pytest
from pathlib import Path
from core.ingestion import load_and_split

FIXTURES = Path(__file__).parent / "fixtures"


def test_load_txt():
    chunks, doc_id = load_and_split(str(FIXTURES / "sample.txt"))
    assert len(chunks) > 0
    assert doc_id is not None


def test_load_md():
    chunks, doc_id = load_and_split(str(FIXTURES / "sample.md"))
    assert len(chunks) > 0


def test_unsupported_format():
    with pytest.raises(ValueError):
        load_and_split("some_file.xyz")


def test_chunk_metadata():
    chunks, doc_id = load_and_split(str(FIXTURES / "sample.txt"))
    for i, chunk in enumerate(chunks):
        assert chunk.metadata["doc_id"] == doc_id
        assert chunk.metadata["chunk_index"] == i
