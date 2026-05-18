# Implementation Guide

**Project:** MindVault — Personal Knowledge Base Chatbot
**Platform:** Ubuntu 22.04 / 24.04
**Stack:** Ollama + RAG + LangChain + ChromaDB + FastAPI + HTML/CSS/JS

---

## Step 0 — Environment Setup

### 0.1 Install System Dependencies

```bash
sudo apt update && sudo apt upgrade -y
sudo apt install -y python3 python3-venv python3-pip git curl build-essential
```

### 0.2 Install Ollama

```bash
curl -fsSL https://ollama.com/install.sh | sh

# Start as a systemd service (survives reboots)
sudo systemctl start ollama
sudo systemctl enable ollama

# Pull the models
ollama pull llama3.2:3b          # Main LLM (~2 GB)
ollama pull nomic-embed-text     # Embedding model (~274 MB)

# Verify
ollama list
```

### 0.3 Create Virtual Environment

```bash
cd mindvault

python3 -m venv venv          # Ubuntu ships Python 3.12
source venv/bin/activate

# You should see (venv) in your prompt
pip install --upgrade pip
```

### 0.4 Install Python Dependencies

```bash
pip install -r requirements.txt
```

Or manually:

```bash
pip install langchain==0.3.* langchain-community==0.3.* langchain-ollama==0.2.* \
            chromadb==0.5.* fastapi==0.115.* uvicorn python-multipart \
            python-dotenv pypdf docx2txt "unstructured[md]" requests pytest
```

### 0.5 Project Structure

```bash
mkdir -p core ui static data/uploads data/chroma_db scripts tests/fixtures
touch server.py .env.example
touch core/__init__.py core/ingestion.py core/embeddings.py
touch core/vector_store.py core/retriever.py core/llm.py core/chain.py
touch ui/__init__.py ui/chat.py ui/sidebar.py ui/styles.py
touch scripts/ingest_folder.py scripts/reset_db.py
touch tests/__init__.py tests/test_ingestion.py tests/test_chain.py
touch static/index.html
```

### 0.6 Create `.env`

```bash
cp .env.example .env
```

Contents of `.env`:

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

## Step 1 — Document Ingestion Pipeline

### `core/ingestion.py`

Loads files, splits into chunks, attaches metadata. Supports PDF, TXT, MD, DOCX, EPUB.

Key details:
- `TextLoader` uses `autodetect_encoding=True` to handle non-UTF8 files
- Empty document guard: raises `ValueError` if no text extracted
- Metadata per chunk: `{source, page, doc_id, chunk_index}`

```python
def load_and_split(file_path, chunk_size=800, chunk_overlap=150) -> tuple[list[Document], str]
def load_folder(folder_path, **kwargs) -> list[tuple[list[Document], str]]
```

---

## Step 2 — Embeddings & Vector Store

### `core/embeddings.py`

```python
def get_embedding_model(model_name=None) -> OllamaEmbeddings
# Uses nomic-embed-text by default (768-dim vectors, fully local)
```

### `core/vector_store.py`

```python
def get_or_create_collection(collection_name, embedding_model, persist_dir=None) -> Chroma
def add_documents(collection, documents) -> None
def delete_document(collection, doc_id) -> None
def list_documents(collection) -> list[dict]   # empty-safe, deduped by doc_id
```

---

## Step 3 — Retriever, LLM, RAG Chain

### `core/retriever.py`

```python
def get_retriever(collection, k=None) -> VectorStoreRetriever
# k reads from RETRIEVAL_K env var (default 5)
# cosine similarity search
```

### `core/llm.py`

```python
def get_llm(model_name=None, temperature=None) -> OllamaLLM
# Reads DEFAULT_LLM_MODEL and LLM_TEMPERATURE from env
```

### `core/chain.py`

```python
def build_rag_chain(llm, retriever, memory_window=None) -> ConversationalRetrievalChain
# ConversationBufferWindowMemory with k=MEMORY_WINDOW (default 5)

def run_chain(chain, question) -> {"answer": str, "sources": list[dict]}
# Deduplicates source excerpts before returning
```

---

## Step 4 — FastAPI Backend

### `server.py`

The single entry point. Holds in-memory app state (chain, collection).

```python
state = {
    "chain": None,
    "collection": None,
    "collection_name": "my_knowledge_base",
    "model": "llama3.2:3b",
}
```

Mounts `./static` directory at `/static` and serves `static/index.html` at `/`.

Full REST API:

```
GET  /                          → static/index.html
GET  /api/health                → {ollama, chain_loaded, collection, model}
POST /api/load                  → {collection_name, model, retrieval_k}
POST /api/ingest                → multipart files + settings
GET  /api/documents             → [{doc_id, source}]
DELETE /api/documents/{doc_id}  → {status}
POST /api/chat                  → {question} → {answer, sources}
POST /api/clear                 → clears chain memory
```

---

## Step 5 — Frontend

### `static/index.html`

Single file — all CSS and JavaScript are inline. No build step, no framework.

**Sidebar (dark navy `#0f172a`):**
- Brand logo + live Ollama status dot
- Collection name input
- Model dropdown (5 options)
- Collapsible RAG settings (chunk size, overlap, top-K sliders)
- Load Collection button
- Drag-and-drop upload zone + file chip list
- Ingest progress bar
- Ingested document list with per-document delete
- Clear Chat button

**Main area (light `#f8fafc`):**
- Topbar: title, collection badge, model badge, Clear button
- Orange offline banner (shown when Ollama unreachable)
- Scrollable chat: user bubbles (right, indigo), bot cards (left, white + shadow)
- Animated thinking dots while waiting for LLM
- Collapsible source citation cards per bot answer
- Auto-resizing textarea — Enter to send, Shift+Enter for newline
- Toast notifications (top-right, auto-dismiss after 3.5s)
- Mobile: hamburger menu, sidebar slides in from left

**JS state machine:**

```javascript
const S = { loaded: false, sending: false, files: [] };
// loaded: true after collection is loaded or ingestion completes
// sending: true while /api/chat is in flight
// files: staged for ingest (not yet uploaded)
```

---

## Step 6 — Utility Scripts

### `scripts/ingest_folder.py`

Bulk ingest a folder from CLI:

```bash
python scripts/ingest_folder.py /path/to/docs --collection my_kb --chunk-size 800
```

### `scripts/reset_db.py`

Wipe the vector store:

```bash
python scripts/reset_db.py --yes
```

---

## Step 7 — Tests

```bash
pytest tests/ -v
```

`tests/test_ingestion.py` — tests `load_and_split` for TXT and MD, metadata correctness, unsupported format rejection.

`tests/test_chain.py` — end-to-end: ingest `sample.txt`, ask a question, assert answer and sources are returned. **Requires Ollama running.**

---

## Step 8 — Run the App

```bash
# Make sure Ollama is running
sudo systemctl start ollama

# Activate venv
source venv/bin/activate

# Start the server
python server.py
```

Open **http://localhost:8000** in your browser.

---

## Quick Validation Checklist

```
[ ] ollama list                  → shows llama3.2:3b and nomic-embed-text
[ ] python server.py             → starts on http://localhost:8000
[ ] Open browser → green dot in sidebar (Ollama connected)
[ ] Drag a PDF onto the upload zone → file chip appears
[ ] Click Ingest → progress bar, success toast, doc appears in list
[ ] Type a question, Enter → thinking dots → answer with sources
[ ] Click source toggle → citation card expands
[ ] Switch model in dropdown, reload collection → new model responds
[ ] Click document × button → doc removed from list
[ ] Resize browser to mobile → hamburger menu appears
```

---

## Troubleshooting

| Problem | Fix |
|---------|-----|
| Orange Ollama banner | `sudo systemctl start ollama` |
| `Model not found` | `ollama pull llama3.2:3b` |
| Slow responses | Switch to `phi3:mini` or `gemma2:2b` |
| `ModuleNotFoundError` | `pip install -r requirements.txt` in venv |
| Port 8000 already in use | Edit `server.py` → change `port=8000` |
| Empty answers | Lower chunk size, raise Top-K, re-ingest |
| ChromaDB error | `pip install "chromadb==0.5.*"` |
| PDF parse fails | `pip install pypdf --upgrade` |
| `unstructured` import error | `pip install "unstructured[md]"` |
