# Architecture

## What existed before, and what changed

The original `app.py` was a single Streamlit script: PyPDF2 extracted
text, LangChain's `RecursiveCharacterTextSplitter` chunked it, a
HuggingFace embedding model embedded it, FAISS indexed it in memory, and
`ConversationalRetrievalChain.from_llm(...)` handled retrieval and
generation as one opaque call. Everything lived in Streamlit's session
state, so it vanished on refresh, supported only PDFs, and had no
concept of separate users.

**What was preserved conceptually:** the pipeline shape (extract → chunk
→ embed → index → retrieve → generate) is the same idea, because it's
the right idea. FAISS is kept from the original design for the same
reason it was chosen then: free, fast enough, easy to explain. The
embedding source itself did change later — see the Deployment section
below for why a hosted API replaced the originally-local model.

**What was rebuilt, and why:** everything that made the old app a demo
rather than a product.
- No persistence → PostgreSQL/SQLite with real tables for users,
  documents, chunks, conversations, messages, and citations.
- No auth → JWT-based auth with per-user data isolation enforced at the
  query level, not just the UI level.
- PDF-only → PyMuPDF, python-docx, pandas, and stdlib parsing cover
  PDF/DOCX/TXT/MD/CSV.
- One LangChain call did everything → chunking, hybrid retrieval, prompt
  construction, and citation mapping are now separate, readable Python
  modules (`app/rag/*.py`) with no LangChain dependency at all, so the
  logic is inspectable and explainable rather than a black box.
- No citations tied to real data → every citation traces back to an
  actual `DocumentChunk` row through a `vector_ref` / `chunk_id`, never
  invented text.

A clean rebuild was the right call here rather than incrementally
patching the Streamlit app, because persistence, auth, and multi-user
isolation are structural requirements that a session-state app can't be
patched into — they have to be there from the database layer up.

## High-level request flow

```
Browser (React)
      │  fetch() with Authorization: Bearer <JWT>
      ▼
FastAPI (app/main.py)
      │
      ├─ app/api/routes/*        (parse request, check ownership, call services)
      ├─ app/core/deps.py        (JWT → current_user, on every protected route)
      ├─ app/services/*          (business logic: validate upload, run pipeline, ask question)
      ├─ app/rag/*               (loaders, chunking, embeddings, vector_store, keyword_search,
      │                            hybrid_search, prompt_builder, citations, pipeline)
      └─ app/models/* + SQLAlchemy → SQLite (dev) / PostgreSQL (prod)
                                   → FAISS index files + SQLite FTS5 (search indexes, on disk)
```

## Backend module map

```
backend/app/
  main.py              FastAPI app, CORS, router registration, startup hook
  config.py            All settings, read from environment / .env
  database.py          SQLAlchemy engine/session (SQLite or Postgres, same code)
  core/
    security.py        Password hashing (bcrypt), JWT encode/decode
    deps.py            get_current_user dependency used by every protected route
  models/              SQLAlchemy ORM models (User, Document, DocumentChunk,
                        Conversation, Message, MessageSource, Feedback)
  schemas/             Pydantic request/response shapes
  api/routes/
    auth.py            /api/auth/register, /login, /me
    documents.py        /api/documents (upload, list, get, delete, reprocess)
    chat.py             /api/chat/conversations, .../ask, .../messages, feedback
    analytics.py        /api/analytics/summary — real counts only
  services/
    document_service.py   upload validation, saving to disk, running the pipeline
    retrieval_service.py  wires the DB + FAISS + FTS5 into one retrieve() call
    chat_service.py       retrieval → prompt → Groq (or extractive fallback) → persist
  rag/                 the hand-built pipeline (see docs/ML_EXPLANATION.md for the "why")
    loaders.py          PDF/DOCX/TXT/MD/CSV → [{"text":..., "page":...}]
    chunking.py          from-scratch recursive splitter, no LangChain
    embeddings.py         Gemini embedding API client (retries, batching, L2-normalize —
                           not a local model; see docs/ML_EXPLANATION.md for why)
    vector_store.py       FAISS index build/search, one index file per document
    keyword_search.py     SQLite FTS5 full-text index
    hybrid_search.py      pure score-merging logic (unit-testable without DB/FAISS)
    prompt_builder.py     system/context/question separation (prompt-injection defense)
    citations.py          retrieved chunks → structured, numbered citations
    pipeline.py            ties ingestion stages together for document_service.py
  evaluation/
    retrieval_metrics.py  recall@k / MRR against a manually verified dataset
    dataset.json           starts empty; see evaluation/README.md
tests/                  40+ pytest tests: unit (chunking, hybrid search, citations,
                        prompt injection, loaders, embedding batching/retries) +
                        API integration (auth, isolation, upload validation, background
                        processing failure handling)
```

## Frontend module map

```
frontend/src/
  App.jsx              Routes, ProtectedRoute / PublicOnlyRoute guards
  hooks/useAuth.jsx     Auth context: login/register/logout, current user
  services/api.js       Thin fetch wrapper: attaches JWT, normalizes errors
  components/
    Sidebar.jsx, AppShell.jsx   Navigation shell for authenticated pages
    ChatMessage.jsx             Message bubble + citation chips + feedback buttons
    ui.jsx                      Buttons, badges, empty states, spinners, error banner
  pages/
    Landing.jsx          Public marketing page (SEO meta tags in index.html)
    Login.jsx / Register.jsx
    Dashboard.jsx        Real stats from /api/analytics/summary, recent documents
    Documents.jsx         Upload (drag-and-drop + browse), list, delete, status
    Chat.jsx              Conversation list, document selection, ask/answer/citations
    History.jsx           Search/rename*/delete conversations (*rename not yet wired to backend)
    Analytics.jsx          Real usage numbers; explains where dev-only eval metrics live
    Settings.jsx           Profile, privacy note, logout
```

## Database schema (see `app/models/`)

```
users(id, name, email, password_hash, created_at)
documents(id, user_id→users, file_name, file_type, file_path, file_size,
          page_count, processing_status, processing_error, created_at, updated_at)
document_chunks(id, document_id→documents, chunk_index, content, page_number, vector_ref)
conversations(id, user_id→users, title, document_ids [comma-separated], created_at, updated_at)
messages(id, conversation_id→conversations, role, content, created_at)
message_sources(id, message_id→messages, chunk_id→document_chunks, relevance_score, citation_order)
feedback(id, user_id→users, message_id→messages, rating, comment, created_at)
```

`vector_ref` on `document_chunks` is the row index of that chunk's
embedding inside its document's FAISS index — this is the concrete
mechanism that makes "every citation traceable to real source text" true
rather than aspirational: a retrieved FAISS hit is a `(document_id,
vector_ref)` pair, which is looked up directly against this column.

## Storage layout

```
backend/storage/
  uploads/<user_id>/<uuid>.<ext>      raw uploaded files, never trusting the original filename
  vector_indexes/<document_id>.index  one FAISS index per document
  vector_indexes/keyword_index.db     shared SQLite FTS5 index (chunks tagged by document_id)
```

## Security model

- Passwords: bcrypt via passlib (`app/core/security.py`).
- Sessions: stateless JWT, 24h expiry, `HS256`, signed with `SECRET_KEY`
  from environment (never hardcoded, never committed).
- Authorization: every document/conversation query filters by
  `user_id == current_user.id`; a request for someone else's resource
  returns 404 (not 403), so resource existence isn't leaked either.
- File uploads: extension allowlist, size limit, and the file is saved
  under a randomly generated name — the original filename is stored in
  the DB for display but never used to build a filesystem path.
- Prompt injection: see `app/rag/prompt_builder.py`'s docstring and
  `docs/ML_EXPLANATION.md` — retrieved document text is kept in its own
  delimited block, separate from the fixed system instructions.

## Deployment

Live at **[talkify-v2-0.vercel.app](https://talkify-v2-0.vercel.app)**
(frontend, on Vercel) talking to **[talkify-v2-0-backend.onrender.com](https://talkify-v2-0-backend.onrender.com)**
(backend, on Render's free tier), with Neon for Postgres — all three
genuinely free, no card on file anywhere.

`docker-compose.yml` at the repo root also works for running the whole
stack (Postgres + backend + frontend) locally in containers, useful for
development without touching any cloud service at all.

### Getting to a stable free deployment took real debugging, not just config

This is worth documenting honestly because each problem was a distinct,
real production issue with a specific root cause — not vague "it didn't
work" trial and error:

1. **A version-pinning bug caused silent 404s on every auth route.**
   Installing FastAPI without an exact pin (`pip install fastapi` instead
   of `pip install -r requirements.txt`) pulled a materially newer
   release with different internal router registration — the server
   started and logged normally, but `/api/auth/login` genuinely didn't
   exist on the running app. Fixed by pinning `fastapi` and `starlette`
   together, and added `scripts/verify_setup.py` to catch this exact
   failure mode by name if it recurs.
2. **Neon's pooled endpoint silently drops idle connections.** Between
   marking a document "processing" and finishing embedding, there's a
   real gap with no database activity — long enough for Neon's PgBouncer
   layer to close the connection. SQLAlchemy had no way to know, so the
   next query threw, and — the actual bug — that exception wasn't caught
   anywhere in the background task, leaving documents stuck on
   "processing" forever with no error surfaced anywhere. Fixed with
   `pool_pre_ping` + `pool_recycle` in `database.py`, and a proper
   try/except in the background task that guarantees a document ends up
   `failed` with a real message using a *fresh* connection, rather than
   silently hanging (see `api/routes/documents.py::_mark_failed`).
3. **PyTorch doesn't fit in a free host's memory budget, at any model
   size.** `sentence-transformers` plus PyTorch needs 200MB-1GB+ of
   resident memory just to run, and every card-free free hosting tier in
   2026 caps around 512MB — the OS OOM-killed the container mid-request
   regardless of how aggressively the model itself was shrunk or how
   many threads were limited. The actual fix was architectural, not a
   tuning knob: removing PyTorch entirely and calling Google's Gemini
   embedding API instead. Measured result: backend RSS dropped from
   OOM-crashing 512MB+ to **~147MB** — verified with
   `/proc/<pid>/status`, not estimated.

See `docs/INTERVIEW_PREPARATION.md` for how to talk through this
sequence in an interview — it's a more interesting story than "it
deployed on the first try."
