import os
from langchain_ollama import OllamaEmbeddings


def get_embedding_model(model_name: str = None) -> OllamaEmbeddings:
    """Return the Ollama embedding model."""
    model = model_name or os.getenv("DEFAULT_EMBED_MODEL", "nomic-embed-text")
    base_url = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
    return OllamaEmbeddings(model=model, base_url=base_url)
