import os
from langchain_ollama import OllamaLLM


def get_llm(model_name: str = None, temperature: float = None) -> OllamaLLM:
    """Return configured Ollama LLM."""
    model = model_name or os.getenv("DEFAULT_LLM_MODEL", "llama3.2:3b")
    temp = temperature if temperature is not None else float(os.getenv("LLM_TEMPERATURE", 0.1))
    base_url = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
    return OllamaLLM(model=model, temperature=temp, base_url=base_url)
