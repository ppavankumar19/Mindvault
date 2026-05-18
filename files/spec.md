# Technical Specification

**Project:** MindVault — Personal Knowledge Base Chatbot
**Version:** 1.0
**Stack:** Ollama + RAG + LangChain + ChromaDB + FastAPI + HTML/CSS/JS

---

## 1. System Architecture

### 1.1 Overview

```
┌─────────────────────────────────────────────────────────┐
│                    Browser (port 8000)                   │
│              static/index.html  (SPA)                    │
│         HTML + CSS + Vanilla JS — fetch() API calls      │
└───────────────────────┬─────────────────────────────────┘
                        │ HTTP REST
                        ▼
┌─────────────────────────────────────────────────────────┐
│                  FastAPI  server.py                      │
│                                                          │
│  GET  /               → serves index.html               │
│  GET  /api/health     → Ollama + chain status           │
│  POST /api/load       → init collection + RAG chain     │
│  POST /api/ingest     → upload + embed + store docs     │
│  GET  /api/documents  → list ingested docs              │
│  DELETE /api/documents/{id} → remove doc chunks         │
│  POST /api/chat       → question → answer + sources     │
│  POST /api/clear      → clear conversation memory       │
└──────────┬────────────────────────┬─────────────────────┘
           │                        │
     Ingestion Pipeline         RAG Query Pipeline
           │                        │
           ▼                        ▼
┌──────────────────┐     ┌──────────────────────────┐
│  core/ingestion  │     │  core/chain (RAG Chain)   │
│  Load → Chunk    │     │                           │
│  → Embed → Store │     │  1. Embed user query      │
└────────┬─────────┘     │  2. ChromaDB similarity   │
         │               │     search → top-K chunks  │
         ▼               │  3. Build prompt + history │
┌──────────────────┐     │  4. Send to Ollama LLM    │
│    ChromaDB      │◄────┤  5. Return answer + cites │
│  (data/chroma_db)│     └────────────┬──────────────┘
└──────────────────┘                  │
                                      ▼
                           ┌─────────────────────┐
                           │   Ollama  :11434     │
                           │   llama3.2:3b        │
                           │   nomic-embed-text   │
                           └─────────────────────┘
```

### 1.2 Data Flow

**Ingestion:**
```
Uploaded file (PDF / TXT / MD / DOCX)
    → core/ingestion.py  load_document()   raw text + metadata
    → split_documents()                    chunks with doc_id, chunk_index
    → core/embeddings.py get_embedding_model()  nomic-embed-text via Ollama
    → core/vector_store.py add_documents()      stored in ChromaDB collection
```

**Query:**
```
User question (string)
    → core/embeddings.py   embed question → 768-dim vector
    → ChromaDB             cosine similarity → top-K chunks
    → core/chain.py        system_prompt + history + chunks + question
    → Ollama LLM           answer string
    → run_chain()          { answer, sources: [{doc_name, page, excerpt}] }
    → /api/chat response   JSON to browser
```

---

## 2. Technology Stack

| Layer | Technology | Version | Purpose |
|-------|-----------|---------|---------|
| LLM Runtime | Ollama | Latest | Run local LLMs |
| LLM Model | llama3.2:3b (default) | — | Answer generation |
| Embedding Model | nomic-embed-text | — | Text → 768-dim vectors |
| RAG Orchestration | LangChain | 0.3.x | Chain, memory, prompt |
| Vector Store | ChromaDB | 0.5.x | Local embedding database |
| Document Loaders | LangChain Community | 0.3.x | PDF, DOCX, MD, TXT |
| Text Splitter | RecursiveCharacterTextSplitter | — | Chunking strategy |
| API Framework | FastAPI | 0.115.x | REST backend |
| ASGI Server | Uvicorn | 0.30.x | Serve FastAPI |
| Frontend | HTML + CSS + Vanilla JS | — | Single-page app |
| Language | Python | 3.12 | Backend |
| Env Config | python-dotenv | 1.0.x | `.env` loading |
| Testing | pytest | 8.x | Unit tests |

---

## 3. Backend Module Specifications

### 3.1 `server.py` — FastAPI Application

**In-memory state** (single-user, process-scoped):

```python
state = {
    "chain": None,           # ConversationalRetrievalChain | None
    "collection": None,      # Chroma collection | None
    "collection_name": str,  # active collection name
    "model": str,            # active LLM model name
}
```

**Endpoints:**

| Endpoint | Method | Body / Params | Response |
|----------|--------|---------------|----------|
| `/` | GET | — | `index.html` |
| `/api/health` | GET | — | `{ollama, chain_loaded, collection, model}` |
| `/api/load` | POST | `{collection_name, model, retrieval_k}` | `{status, collection, doc_count}` |
| `/api/ingest` | POST | multipart: `files[]`, `collection_name`, `model`, `chunk_size`, `chunk_overlap`, `retrieval_k` | `{results: [{file, chunks, status}]}` |
| `/api/documents` | GET | — | `{documents: [{doc_id, source}]}` |
| `/api/documents/{doc_id}` | DELETE | — | `{status}` |
| `/api/chat` | POST | `{question}` | `{answer, sources}` |
| `/api/clear` | POST | — | `{status}` |

---

### 3.2 `core/ingestion.py`

**Responsibility:** Load files, split into chunks, attach metadata.

**Supported formats:**

| Extension | Loader |
|-----------|--------|
| `.pdf` | `PyPDFLoader` |
| `.txt` | `TextLoader` (autodetect encoding) |
| `.md` | `UnstructuredMarkdownLoader` |
| `.docx` | `Docx2txtLoader` |
| `.epub` | `UnstructuredEPubLoader` |

**Chunking:**
- Splitter: `RecursiveCharacterTextSplitter`
- Default chunk size: `800` chars
- Default overlap: `150` chars
- Metadata per chunk: `{source, page, doc_id, chunk_index}`
- Guard: raises `ValueError` if extracted text is empty

**Interface:**
```python
def load_and_split(file_path, chunk_size=800, chunk_overlap=150) -> tuple[list[Document], str]
def load_folder(folder_path, **kwargs) -> list[tuple[list[Document], str]]
```

---

### 3.3 `core/embeddings.py`

```python
def get_embedding_model(model_name=None) -> OllamaEmbeddings
# model: nomic-embed-text (768-dim), reads OLLAMA_BASE_URL from env
```

---

### 3.4 `core/vector_store.py`

```python
def get_or_create_collection(collection_name, embedding_model, persist_dir=None) -> Chroma
def add_documents(collection, documents) -> None
def delete_document(collection, doc_id) -> None        # deletes by doc_id metadata field
def list_documents(collection) -> list[dict]           # [{doc_id, source}], deduped, empty-safe
```

Storage: `./data/chroma_db/` (configurable via `CHROMA_PERSIST_DIR`)

---

### 3.5 `core/retriever.py`

```python
def get_retriever(collection, k=None) -> VectorStoreRetriever
# k defaults to RETRIEVAL_K env var (default 5)
# algorithm: cosine similarity
```

---

### 3.6 `core/llm.py`

```python
def get_llm(model_name=None, temperature=None) -> OllamaLLM
# model: DEFAULT_LLM_MODEL env var (default llama3.2:3b)
# temperature: LLM_TEMPERATURE env var (default 0.1)
```

---

### 3.7 `core/chain.py`

**Chain type:** `ConversationalRetrievalChain`
**Memory:** `ConversationBufferWindowMemory` — last K exchanges (default 5)

**System prompt template:**
```
You are a helpful assistant that answers questions based on the provided documents.

Rules:
- Answer ONLY using information from the provided context.
- If the answer is not in the context, say: "I don't have enough information..."
- Be concise and clear.
- Cite the source document and page number at the end.

Context: {context}
Question: {question}
Answer:
```

**Interface:**
```python
def build_rag_chain(llm, retriever, memory_window=None) -> ConversationalRetrievalChain
def run_chain(chain, question) -> {"answer": str, "sources": list[dict]}
# sources deduped by excerpt; each: {doc_name, page, excerpt}
```

---

## 4. Frontend — `static/index.html`

Single file, no build step, no framework. All CSS and JS are inline.

### Layout

```
┌─────────────────────────────────────────────────────────┐
│  Sidebar (288px, dark)  │  Main area (flex-1, light)    │
│                         │                               │
│  Brand + Ollama dot     │  Topbar: title, badges, Clear │
│  Collection input       │  Alert banner (if offline)    │
│  Model dropdown         │                               │
│  RAG settings (toggle)  │  Chat scroll area:            │
│  Load Collection btn    │    Empty state (first visit)  │
│  ─────────────────────  │    User bubbles (right, blue) │
│  Upload drop zone       │    Bot cards (left, white)    │
│  File chips             │    Source citation toggles    │
│  Progress bar           │    Thinking animation         │
│  Ingest button          │                               │
│  ─────────────────────  │  Input bar:                   │
│  Document list + delete │    Textarea + Send button     │
│  ─────────────────────  │    Hint text                  │
│  Clear Chat button      │                               │
└─────────────────────────┴───────────────────────────────┘
```

### JS Architecture

| Component | Description |
|-----------|-------------|
| `state {}` | `{ loaded, sending, files[] }` |
| `checkHealth()` | polls `/api/health` every 15s, updates status dot + alert |
| `loadCollection()` | calls `POST /api/load`, enables send button |
| `addFiles() / removeFile()` | manages staged file list |
| `ingest()` | `POST /api/ingest` with FormData, animates progress bar |
| `loadDocs()` | `GET /api/documents`, renders doc list with delete buttons |
| `send()` | `POST /api/chat`, renders thinking → answer → sources |
| `clearChat()` | clears DOM + calls `POST /api/clear` |
| `toggleSrc()` | expand/collapse source citation panel per message |

### CSS Design Tokens

| Token | Value | Usage |
|-------|-------|-------|
| `--sb` | `#0f172a` | Sidebar background |
| `--accent` | `#6366f1` | Buttons, badges, links |
| `--user-bg` | `#6366f1` | User chat bubbles |
| `--bot-bg` | `#ffffff` | Bot message cards |
| `--main-bg` | `#f8fafc` | Page background |
| `--border` | `#e2e8f0` | Dividers, input borders |

---

## 5. Configuration (`.env`)

```env
OLLAMA_BASE_URL=http://localhost:11434
DEFAULT_LLM_MODEL=llama3.2:3b
DEFAULT_EMBED_MODEL=nomic-embed-text
LLM_TEMPERATURE=0.1
CHROMA_PERSIST_DIR=./data/chroma_db
DEFAULT_COLLECTION=my_knowledge_base
CHUNK_SIZE=800
CHUNK_OVERLAP=150
RETRIEVAL_K=5
MEMORY_WINDOW=5
MAX_UPLOAD_SIZE_MB=50
UPLOAD_DIR=./data/uploads
```

---

## 6. API Response Contracts

### `POST /api/ingest`
```json
{
  "results": [
    { "file": "report.pdf", "chunks": 142, "status": "ok" },
    { "file": "bad.xyz",    "error": "Unsupported file type", "status": "error" }
  ]
}
```

### `POST /api/chat`
```json
{
  "answer": "The document explains that...",
  "sources": [
    { "doc_name": "report.pdf", "page": 12, "excerpt": "...relevant passage..." }
  ]
}
```

### `GET /api/health`
```json
{
  "ollama": true,
  "chain_loaded": true,
  "collection": "my_knowledge_base",
  "model": "llama3.2:3b"
}
```

---

## 7. Performance Targets

| Metric | Target |
|--------|--------|
| Ingestion speed | ≥ 10 pages/second on CPU |
| First token latency (3B model, CPU) | < 5 seconds |
| Full response (3B model, CPU) | < 30 seconds |
| Retrieval latency (ChromaDB) | < 200 ms |
| Max supported document size | 500 pages / 50 MB |
| API response for `/api/health` | < 500 ms |

---

## 8. Error Handling

| Scenario | Behavior |
|---------|----------|
| Ollama not running | `/api/health` returns `ollama: false`; browser shows orange banner |
| No collection loaded | `/api/chat` returns HTTP 400 with clear message |
| Unsupported file type | `ingestion.py` raises `ValueError`; returned as `status: error` per file |
| Empty document after parsing | `ingestion.py` raises `ValueError` with filename |
| LLM / chain error | `/api/chat` returns HTTP 500 with error detail |
| Document not found for delete | HTTP 404 |
| ChromaDB write failure | Exception caught, returned as error JSON |

---

## 9. Testing

```
tests/
├── test_ingestion.py    # load_and_split for TXT, MD; metadata checks; unsupported format
├── test_chain.py        # end-to-end Q&A on sample.txt via rag_chain fixture
└── fixtures/
    ├── sample.txt       # RAG explanation text
    └── sample.md        # Markdown chunking + retrieval test
```

Run:
```bash
pytest tests/ -v
```

Note: `test_chain.py` requires Ollama running with `llama3.2:3b` and `nomic-embed-text`.

---

## 10. Dependencies (`requirements.txt`)

```
langchain==0.3.*
langchain-community==0.3.*
langchain-ollama==0.2.*
chromadb==0.5.*
python-dotenv==1.0.*
pypdf==4.*
docx2txt==0.8
unstructured[md,epub]==0.14.*
pytest==8.*
fastapi==0.115.*
uvicorn==0.30.*
python-multipart==0.0.*
requests==2.*
```

---

## 11. Security Considerations

- All data stored locally — no external network calls after model pull
- Filenames sanitized via `tempfile.NamedTemporaryFile` on upload (no path traversal)
- No authentication needed (single-user, local-only app)
- CORS middleware allows all origins (localhost use only — do not expose publicly)
