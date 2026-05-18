import os
import tempfile
from pathlib import Path

import requests as http
from fastapi import FastAPI, UploadFile, File, HTTPException, Form
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from dotenv import load_dotenv

load_dotenv()

from core.ingestion import load_and_split
from core.embeddings import get_embedding_model
from core.vector_store import get_or_create_collection, add_documents, list_documents, delete_document
from core.retriever import get_retriever
from core.llm import get_llm
from core.chain import build_rag_chain, run_chain

# ── In-memory app state ───────────────────────────────────────────
state: dict = {
    "chain": None,
    "collection": None,
    "collection_name": os.getenv("DEFAULT_COLLECTION", "my_knowledge_base"),
    "model": os.getenv("DEFAULT_LLM_MODEL", "llama3.2:3b"),
}

app = FastAPI(title="MindVault API", version="1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.mount("/static", StaticFiles(directory="static"), name="static")


# ── Serve frontend ────────────────────────────────────────────────
@app.get("/")
def index():
    return FileResponse("static/index.html")


# ── Health ────────────────────────────────────────────────────────
@app.get("/api/health")
def health():
    try:
        r = http.get(os.getenv("OLLAMA_BASE_URL", "http://localhost:11434"), timeout=2)
        ollama_ok = r.status_code == 200
    except Exception:
        ollama_ok = False
    return {
        "ollama": ollama_ok,
        "chain_loaded": state["chain"] is not None,
        "collection": state["collection_name"],
        "model": state["model"],
    }


# ── Load collection ───────────────────────────────────────────────
class LoadRequest(BaseModel):
    collection_name: str
    model: str
    retrieval_k: int = 5


@app.post("/api/load")
def load_collection(req: LoadRequest):
    try:
        embed_model = get_embedding_model()
        collection = get_or_create_collection(req.collection_name, embed_model)
        llm = get_llm(req.model)
        retriever = get_retriever(collection, req.retrieval_k)
        chain = build_rag_chain(llm, retriever)

        state["chain"] = chain
        state["collection"] = collection
        state["collection_name"] = req.collection_name
        state["model"] = req.model

        docs = list_documents(collection)
        return {"status": "ok", "collection": req.collection_name, "doc_count": len(docs)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ── Ingest documents ──────────────────────────────────────────────
@app.post("/api/ingest")
async def ingest(
    files: list[UploadFile] = File(...),
    collection_name: str = Form(...),
    model: str = Form(...),
    chunk_size: int = Form(800),
    chunk_overlap: int = Form(150),
    retrieval_k: int = Form(5),
):
    embed_model = get_embedding_model()
    collection = get_or_create_collection(collection_name, embed_model)

    results = []
    for file in files:
        suffix = Path(file.filename).suffix
        with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
            tmp.write(await file.read())
            tmp_path = tmp.name

        try:
            chunks, doc_id = load_and_split(tmp_path, chunk_size, chunk_overlap)
            for chunk in chunks:
                chunk.metadata["source"] = file.filename
            add_documents(collection, chunks)
            results.append({"file": file.filename, "chunks": len(chunks), "status": "ok"})
        except Exception as e:
            results.append({"file": file.filename, "error": str(e), "status": "error"})
        finally:
            os.unlink(tmp_path)

    # Rebuild chain with updated collection
    llm = get_llm(model)
    retriever = get_retriever(collection, retrieval_k)
    state["chain"] = build_rag_chain(llm, retriever)
    state["collection"] = collection
    state["collection_name"] = collection_name
    state["model"] = model

    return {"results": results}


# ── List documents ────────────────────────────────────────────────
@app.get("/api/documents")
def get_documents():
    if state["collection"] is None:
        return {"documents": []}
    return {"documents": list_documents(state["collection"])}


# ── Delete document ───────────────────────────────────────────────
@app.delete("/api/documents/{doc_id}")
def remove_document(doc_id: str):
    if state["collection"] is None:
        raise HTTPException(status_code=404, detail="No collection loaded")
    delete_document(state["collection"], doc_id)
    return {"status": "deleted"}


# ── Chat ──────────────────────────────────────────────────────────
class ChatRequest(BaseModel):
    question: str


@app.post("/api/chat")
def chat(req: ChatRequest):
    if state["chain"] is None:
        raise HTTPException(
            status_code=400,
            detail="No collection loaded. Upload documents and click Ingest first.",
        )
    try:
        result = run_chain(state["chain"], req.question)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ── Clear chat memory ─────────────────────────────────────────────
@app.post("/api/clear")
def clear_chat():
    if state["chain"] is not None:
        try:
            state["chain"].memory.clear()
        except Exception:
            pass
    return {"status": "cleared"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000, reload=False)
