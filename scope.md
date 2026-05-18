# Project Scope

**Project:** MindVault — Personal Knowledge Base Chatbot
**Platform:** Ubuntu (local machine)
**Stack:** Ollama + RAG + LangChain + ChromaDB + FastAPI + Vanilla HTML/CSS/JS
**Version:** 1.0

---

## Project Goal

Build a **locally running, privacy-first chatbot** that allows a user to:
1. Upload their own documents (PDFs, notes, books)
2. Ask natural language questions about the content
3. Receive accurate, cited answers — without internet access or paid APIs

---

## In Scope

### Core Functionality
- [x] Upload and process documents (PDF, TXT, MD, DOCX, EPUB)
- [x] Chunk documents into semantically meaningful segments
- [x] Generate and store embeddings in a local vector database (ChromaDB)
- [x] Accept user questions via a chat interface
- [x] Retrieve top-K relevant chunks using semantic similarity
- [x] Generate grounded answers using a locally running Ollama LLM
- [x] Display source references (document name + page number) with each answer
- [x] Maintain short-term conversation history (last N turns)
- [x] Support multiple Ollama models (switchable in UI)
- [x] Persist the vector store across sessions (no need to re-ingest)
- [x] Empty-document guard in ingestion pipeline
- [x] Duplicate source deduplication in chain responses

### Document Management
- [x] Upload documents via drag-and-drop or file picker
- [x] List ingested documents in the sidebar
- [x] Delete individual documents from the vector store
- [x] Group documents into named collections
- [x] Bulk ingest a local folder via CLI script

### UI
- [x] Single-page HTML/CSS/JS frontend (no framework)
- [x] Dark sidebar + light main chat area
- [x] Drag-and-drop upload zone with file chip previews
- [x] Ingest progress bar
- [x] Model selector dropdown (5 Ollama models)
- [x] Collapsible advanced RAG settings (chunk size, overlap, top-K)
- [x] Load / reload collection button
- [x] Clear chat history button
- [x] Ollama live status indicator (green/red dot)
- [x] Ollama offline warning banner
- [x] Animated thinking indicator while LLM responds
- [x] Collapsible source citation cards per answer
- [x] Toast notifications for all actions
- [x] Responsive layout — mobile hamburger menu
- [x] Auto-resizing textarea input, Enter to send

### Backend (FastAPI)
- [x] REST API serving the single-page frontend
- [x] `POST /api/load` — initialize collection + chain
- [x] `POST /api/ingest` — multipart file upload + ingestion
- [x] `GET /api/documents` — list documents in active collection
- [x] `DELETE /api/documents/{doc_id}` — remove document
- [x] `POST /api/chat` — question → answer + sources
- [x] `POST /api/clear` — clear conversation memory
- [x] `GET /api/health` — Ollama + chain status check

### Infrastructure
- [x] Works fully offline on Ubuntu 22.04/24.04
- [x] Setup via virtualenv + pip
- [x] `.env` file for configuration
- [x] Unit tests for ingestion and chain

---

## Out of Scope (v1.0)

| Feature | Reason Excluded |
|---------|----------------|
| Fine-tuning the LLM | Covered in v2.0 |
| Multi-user support / auth | Single-user local app |
| Cloud deployment | Intentionally local-only |
| Voice input/output | Future enhancement |
| Web scraping / URL ingestion | Phase 2 |
| Image/diagram understanding (multimodal) | Requires larger models |
| Real-time document syncing | Out of scope |
| Windows/macOS support | Ubuntu focus in v1 |
| Streaming LLM responses | Phase 2 |

---

## Deliverables

| Deliverable | Description |
|------------|-------------|
| `server.py` | FastAPI backend — REST API + static file serving |
| `static/index.html` | Single-page frontend (HTML + CSS + JS) |
| `core/` | Ingestion, embedding, retrieval, LLM, chain modules |
| `ui/` | Legacy Streamlit components (kept for reference) |
| `scripts/` | CLI tools for bulk ingestion and DB reset |
| `tests/` | Unit tests for core modules |
| `README.md` | Setup, usage, RAG explanation, model guide |
| `.env.example` | Configuration template |
| `requirements.txt` | Python dependencies |

---

## Milestones

### Phase 1 — Foundation
- [x] Environment setup (Ollama, Python, dependencies)
- [x] Document ingestion pipeline (load → chunk → embed → store)
- [x] Basic retrieval and Q&A (core modules)
- [x] Verify ingestion with test fixtures

### Phase 2 — RAG Chain
- [x] LangChain RAG chain wired to Ollama
- [x] Conversation memory integrated
- [x] Source citations in responses
- [ ] Unit tests passing (requires Ollama running)

### Phase 3 — UI & API
- [x] FastAPI backend with full REST API
- [x] Single-page HTML/CSS/JS frontend
- [x] Upload, ingest, chat, delete — all wired end-to-end
- [x] Model switcher, RAG settings, collection management
- [x] Responsive design, toast notifications, health check

### Phase 4 — Polish & Testing
- [ ] End-to-end testing with real documents
- [ ] Performance tuning (chunk size, overlap, K)
- [ ] Error handling edge cases
- [ ] Documentation finalized

---

## Success Criteria

1. A user can upload a 200-page PDF and ask questions about it within 60 seconds of upload.
2. Answers are **grounded** — hallucinated content not present in the docs is minimal.
3. Every answer includes a **source citation** (doc name + page).
4. The app runs **entirely offline** with no external API calls.
5. The app starts on a fresh Ubuntu machine after following the README.
6. All unit tests pass (`pytest tests/`).

---

## Risks & Mitigations

| Risk | Likelihood | Impact | Mitigation |
|------|-----------|--------|-----------|
| Ollama model too slow on CPU | High | Medium | Use 3B models; shown in model selector |
| Poor retrieval quality | Medium | High | Tune chunk size, overlap, K via UI sliders |
| Large PDFs causing memory issues | Medium | Medium | Stream-process; guard against empty docs |
| ChromaDB corruption on crash | Low | High | `scripts/reset_db.py` for clean reset |
| Embedding model mismatch after upgrade | Low | High | Lock model name in `.env` |

---

## Future Scope (v2.0 Ideas)

- Streaming LLM responses (token-by-token via SSE)
- Web URL and YouTube transcript ingestion
- Voice interface (Whisper STT + TTS)
- Graph-based knowledge relationships (GraphRAG)
- Multi-user support with authentication
- Export conversations as Markdown/PDF
- Fine-tuning on personal writing style
