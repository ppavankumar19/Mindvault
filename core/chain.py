import os
from langchain.chains import ConversationalRetrievalChain
from langchain.memory import ConversationBufferWindowMemory
from langchain.prompts import PromptTemplate


SYSTEM_PROMPT = """You are a helpful assistant that answers questions based on the provided documents.

Rules:
- Answer ONLY using information from the provided context.
- If the answer is not in the context, say: "I don't have enough information in my knowledge base to answer that."
- Be concise and clear.
- At the end of your answer, cite the source(s): document name and page number if available.

Context:
{context}

Question: {question}

Answer:"""

QA_PROMPT = PromptTemplate(
    template=SYSTEM_PROMPT,
    input_variables=["context", "question"],
)


def build_rag_chain(llm, retriever, memory_window: int = None) -> ConversationalRetrievalChain:
    """Build the full conversational RAG chain."""
    window = memory_window or int(os.getenv("MEMORY_WINDOW", 5))

    memory = ConversationBufferWindowMemory(
        k=window,
        memory_key="chat_history",
        return_messages=True,
        output_key="answer",
    )

    chain = ConversationalRetrievalChain.from_llm(
        llm=llm,
        retriever=retriever,
        memory=memory,
        combine_docs_chain_kwargs={"prompt": QA_PROMPT},
        return_source_documents=True,
        verbose=False,
    )

    return chain


def run_chain(chain: ConversationalRetrievalChain, question: str) -> dict:
    """Run a question through the chain. Returns answer + sources."""
    result = chain.invoke({"question": question})

    sources = []
    seen_excerpts = set()
    for doc in result.get("source_documents", []):
        excerpt = doc.page_content[:200]
        if excerpt in seen_excerpts:
            continue
        seen_excerpts.add(excerpt)
        sources.append({
            "doc_name": os.path.basename(doc.metadata.get("source", "unknown")),
            "page": doc.metadata.get("page", "—"),
            "excerpt": excerpt + "...",
        })

    return {
        "answer": result["answer"],
        "sources": sources,
    }
