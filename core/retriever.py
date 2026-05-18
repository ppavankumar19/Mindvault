import os
from langchain_community.vectorstores import Chroma
from langchain.schema.vectorstore import VectorStoreRetriever


def get_retriever(collection: Chroma, k: int = None) -> VectorStoreRetriever:
    """Return a LangChain retriever for the given collection."""
    top_k = k or int(os.getenv("RETRIEVAL_K", 5))
    return collection.as_retriever(search_kwargs={"k": top_k})
