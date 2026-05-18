# MindVault — Personal Knowledge Base Chatbot

> Chat with your PDFs, notes, and books — fully local, fully private, powered by Ollama + RAG.

![Python](https://img.shields.io/badge/Python-3.12+-blue?logo=python)
![Ollama](https://img.shields.io/badge/Ollama-Local%20LLM-black?logo=ollama)
![LangChain](https://img.shields.io/badge/LangChain-RAG-green)
![ChromaDB](https://img.shields.io/badge/ChromaDB-VectorStore-orange)
![FastAPI](https://img.shields.io/badge/API-FastAPI-teal)
![License](https://img.shields.io/badge/License-MIT-lightgrey)

---

## What Is This?

**MindVault** is a fully offline, privacy-first AI chatbot that lets you upload your personal documents (PDFs, Markdown notes, text files, DOCX) and have an intelligent conversation with them — no internet required, no API costs, no data leaving your machine.

The frontend is a single HTML/CSS/JS page. The backend is a FastAPI server. Everything runs locally.

---

## What Is RAG?

**RAG (Retrieval-Augmented Generation)** is the core technique powering this project.

### The Problem with LLMs Alone

Large language models (LLMs) like Llama or Mistral are trained on general internet data. They don't know about *your* documents — your research papers, your notes, your private PDFs. If you just ask a plain LLM "What does my book say about X?", it will either hallucinate an answer or admit it doesn't know.

### How RAG Solves It

RAG gives the LLM *memory by retrieval*. Instead of baking your documents into the model (which would require expensive fine-tuning), RAG:

1. **Indexes** your documents as vector embeddings at upload time
2. **Retrieves** the most relevant passages at query time using cosine similarity
3. **Augments** the LLM prompt with those retrieved passages as context
4. **Generates** an answer grounded in what the documents actually say

```
Your Question
    │
    ▼
[Embedding Model] → query vector (768-dim)
    │
    ▼
[ChromaDB] cosine similarity search → top-K most relevant chunks
    │
    ▼
[Prompt Builder] system prompt + retrieved chunks + conversation history
    │
    ▼
[Ollama LLM] → grounded answer + source citations
    │
    ▼
[Browser UI] renders answer with collapsible source cards
```

### Why RAG?

| Approach | Answer Quality | Cost | Privacy | Updatable |
|----------|---------------|------|---------|-----------|
| Plain LLM | Hallucinations | Low | Risk | No |
| Fine-tuning | Good | Very High | Risk | Hard |
| **RAG (this project)** | **Grounded** | **Free** | **100% Local** | **Yes — re-ingest** |

RAG gives near-fine-tuning quality at zero cost and with full privacy.

---

## RAG Implementation in This Project

Here is exactly how RAG is implemented across the codebase, end to end.

### 1. Document Ingestion — `core/ingestion.py`

When you upload a file and click **Ingest**, this pipeline runs:

```
PDF / TXT / MD / DOCX
        │
        ▼
  load_document()          ← picks the right LangChain loader by file extension
        │
        ▼
  split_documents()        ← RecursiveCharacterTextSplitter
        │  chunk_size=800 chars, overlap=150 chars
        │  separators: ["\n\n", "\n", ". ", " ", ""]
        ▼
  chunks[]                 ← each chunk carries metadata:
                              { source, page, doc_id, chunk_index }
```

Each document gets a unique `doc_id` (UUID). Chunks overlap by 150 characters so context is never lost at boundaries.

### 2. Embedding — `core/embeddings.py`

After chunking, every chunk is converted to a 768-dimensional vector:

```python
OllamaEmbeddings(model="nomic-embed-text", base_url="http://localhost:11434")
```

- Runs **locally** via Ollama — no API call, no internet
- Same model is used at query time so vectors are comparable
- 768 dimensions captures semantic meaning, not just keywords

### 3. Vector Store — `core/vector_store.py`

Embeddings are stored in **ChromaDB**, a local persistent vector database:

```python
Chroma(
    collection_name=collection_name,
    embedding_function=embedding_model,
    persist_directory="./data/chroma_db",
)
```

- Collections map to named knowledge bases (configurable in the UI)
- Data persists to disk — no need to re-ingest on restart
- Supports multiple collections (e.g. one per project or topic)

### 4. Retrieval — `core/retriever.py`

At query time, the user's question is embedded with the same model and compared against all stored chunk vectors using **cosine similarity**:

```
User question
      │
      ▼
nomic-embed-text → 768-dim query vector
      │
      ▼
ChromaDB cosine similarity search
      │
      ▼
top-K most relevant chunks (default K=5, adjustable in UI)
```

Cosine similarity finds chunks that are *semantically* close to the question — not just matching keywords.

### 5. Prompt Construction — `core/chain.py`

The retrieved chunks are injected into a structured prompt alongside the conversation history:

```
System:
  You are a helpful assistant. Answer ONLY using the provided context.
  If the answer is not in the context, say you don't know.
  Cite the source document and page number at the end.

Context:
  [chunk 1 text]
  [chunk 2 text]
  ...

Conversation History:
  [last 5 exchanges]

Question: {user's question}

Answer:
```

This grounds the LLM — it cannot hallucinate facts that aren't in the retrieved chunks.

### 6. LLM Generation — `core/llm.py`

The prompt is sent to a locally running Ollama model:

```python
OllamaLLM(model="llama3.2:3b", temperature=0.1, base_url="http://localhost:11434")
```

- `temperature=0.1` keeps answers focused and factual (low randomness)
- The model reads the injected context and generates a grounded answer
- Source citations are enforced by the prompt rules

### 7. Conversational Memory — `core/chain.py`

The chain uses `ConversationBufferWindowMemory` to remember the last 5 exchanges:

```python
ConversationBufferWindowMemory(k=5, memory_key="chat_history", return_messages=True)
```

This means follow-up questions work naturally — you can ask "what did it say about X?" and the chain knows what X refers to.

### 8. API Layer — `server.py`

All of the above is exposed through a FastAPI REST backend. The browser talks to it via `fetch()`:

```
Browser                    FastAPI (server.py)             Core Modules
  │                              │                              │
  │── POST /api/ingest ─────────►│── load_and_split() ────────►│ ingestion.py
  │                              │── get_embedding_model() ───►│ embeddings.py
  │                              │── add_documents() ─────────►│ vector_store.py
  │                              │                              │
  │── POST /api/chat ───────────►│── run_chain() ─────────────►│ chain.py
  │◄── { answer, sources } ──────│                              │
```

### Full RAG Flow Summary

```
[Upload file]
      │
      ├── load_document()          core/ingestion.py
      ├── split_documents()        core/ingestion.py
      ├── get_embedding_model()    core/embeddings.py
      └── add_documents()          core/vector_store.py

[Ask question]
      │
      ├── embed question           core/embeddings.py
      ├── cosine similarity search core/retriever.py  → top-K chunks
      ├── build prompt             core/chain.py      → context + history + question
      ├── send to Ollama LLM       core/llm.py        → answer text
      └── return {answer, sources} server.py          → browser renders
```

---

## Models Used

### LLM — Answer Generation

All models run **locally via Ollama**. No API key or internet required after the initial pull.

| Model | Size | Best For |
|-------|------|----------|
| `llama3.2:3b` (default) | ~2 GB | Fast, everyday use on CPU |
| `mistral:7b` | ~4 GB | Better reasoning |
| `phi3:mini` | ~2.3 GB | Low-RAM machines |
| `gemma2:2b` | ~1.6 GB | Lightest option |
| `llama3.1:8b` | ~4.7 GB | Best quality |

**Why small models work well with RAG:** Because RAG injects the relevant document context directly into the prompt, a 3B model can answer accurately — it only needs to *read and synthesize* the provided text, not recall facts from training.

### Embedding Model — Semantic Search

**`nomic-embed-text`** (274 MB) converts text into 768-dimensional vectors.

- Runs locally via Ollama, zero network calls
- Used at ingestion time (embed chunks) and query time (embed the question)
- Cosine similarity between vectors finds semantically related passages, not just keyword matches

---

## System Requirements

| Component | Minimum | Recommended |
|-----------|---------|-------------|
| OS | Ubuntu 22.04 | Ubuntu 24.04 LTS |
| RAM | 8 GB | 16 GB |
| CPU | 4-core | 8-core |
| Storage | 10 GB free | 20 GB free |
| GPU | Optional | NVIDIA (CUDA) for speed |
| Python | 3.12+ | 3.12 |

---

## Quick Start

### 1. Install Ollama and pull models

```bash
curl -fsSL https://ollama.com/install.sh | sh
sudo systemctl start ollama

ollama pull llama3.2:3b        # ~2 GB — main chat model
ollama pull nomic-embed-text   # ~274 MB — embedding model
```

### 2. Setup Python environment

```bash
cd mindvault
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### 3. Configure

```bash
cp .env.example .env
# Defaults work out of the box — edit only if needed
```

### 4. Run

```bash
python server.py
```

Open **http://localhost:8000** in your browser.

---

## Project Structure

```
mindvault/
├── server.py               # FastAPI backend — REST API + serves static/
├── requirements.txt
├── .env / .env.example
│
├── static/
│   └── index.html          # Single-page frontend (HTML + CSS + JS)
│
├── core/
│   ├── ingestion.py        # Document loading, chunking, metadata
│   ├── embeddings.py       # nomic-embed-text via Ollama
│   ├── vector_store.py     # ChromaDB: add, list, delete
│   ├── retriever.py        # Semantic top-K retrieval
│   ├── llm.py              # Ollama LLM wrapper
│   └── chain.py            # RAG chain: build + run
│
├── ui/                     # Legacy Streamlit components (kept for reference)
│   ├── styles.py
│   ├── sidebar.py
│   └── chat.py
│
├── data/
│   ├── uploads/            # Temporary upload staging
│   └── chroma_db/          # Persisted vector store
│
├── scripts/
│   ├── ingest_folder.py    # Bulk CLI ingestion
│   └── reset_db.py         # Wipe vector store
│
└── tests/
    ├── fixtures/           # sample.txt, sample.md
    ├── test_ingestion.py
    └── test_chain.py
```

---

## REST API

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/` | Serves the frontend |
| `GET` | `/api/health` | Ollama + chain status |
| `POST` | `/api/load` | Load/create a collection |
| `POST` | `/api/ingest` | Upload and ingest documents |
| `GET` | `/api/documents` | List ingested documents |
| `DELETE` | `/api/documents/{doc_id}` | Remove a document |
| `POST` | `/api/chat` | Ask a question |
| `POST` | `/api/clear` | Clear conversation memory |

---

## Features

- **Multi-format ingestion** — PDF, Markdown, TXT, DOCX, EPUB
- **Semantic search** — finds relevant passages by meaning, not keywords
- **Conversational memory** — remembers the last 5 exchanges
- **Source citations** — every answer shows which document and page it came from
- **Collection management** — organize docs into named collections
- **Document deletion** — remove individual documents from the vector store
- **Model switcher** — swap Ollama models from the UI without restart
- **Drag-and-drop upload** — drop files directly onto the upload zone
- **Ollama health indicator** — live status dot in the sidebar, warning banner if offline
- **Responsive UI** — dark sidebar + light chat area, works on mobile (hamburger menu)
- **100% offline** — nothing leaves your machine

---

## Troubleshooting

| Problem | Fix |
|---------|-----|
| Ollama warning banner | `sudo systemctl start ollama` |
| `Model not found` | `ollama pull llama3.2:3b` |
| Very slow responses | Switch to `phi3:mini` or `gemma2:2b` in the sidebar |
| `ModuleNotFoundError` | `pip install -r requirements.txt` inside venv |
| Empty answers | Reduce chunk size, increase Top-K, re-ingest |
| ChromaDB error | `pip install "chromadb==0.5.*"` |
| PDF parse fails | `pip install pypdf --upgrade` |
| Port 8000 in use | Edit `server.py` — change `port=8000` to another port |

---

## License

MIT © 2026
