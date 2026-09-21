# Talkify 2.0 — AI Document Intelligence & Research Assistant

Talkify lets you upload documents (PDF, DOCX, TXT, Markdown, CSV) and ask
questions about them in natural language. Answers are grounded in your
documents and come with citations pointing to the exact source page —
not invented, and never from another user's files.

This is version 2.0 of a rebuild from an earlier Streamlit prototype
(`app.py` in the project history). See [`docs/ARCHITECTURE.md`](docs/ARCHITECTURE.md)
for what changed and why.

## Changelog

**Round 2 fixes** (in response to real-world testing):
- **Fixed a 404 on `/api/auth/login` and `/register`.** Root cause found
  and reproduced: an unpinned FastAPI install can silently pull a much
  newer version with different internal routing that drops registered
  routes. `requirements.txt` now pins `starlette` explicitly alongside
  `fastapi` to prevent this, and `scripts/verify_setup.py` is a new
  self-check script that catches this exact problem by name if it
  happens again. See `docs/SETUP.md`'s troubleshooting section.
- **Uploads no longer block the UI.** Processing (chunking, embedding,
  indexing) now runs in a background task; the upload request returns
  immediately and the frontend polls for status.
- **Fixed the "here's what I found" fallback appearing even with an API
  key configured.** Groq quietly moved the previous default model
  (`llama-3.1-8b-instant`) to an Enterprise-only tier; the default is now
  `openai/gpt-oss-20b`, and Groq call failures are now logged server-side
  instead of failing silently, so a future model deprecation is
  diagnosable instead of mysterious.
- **Answers are now rendered as real Markdown** (headings, bold, lists)
  in the chat UI, and the system prompt explicitly asks the model to
  structure longer answers with lists/bold rather than a wall of text.

## Status: honest checklist

This was built in phases. Here's what's actually done vs. not, so nothing
here is overstated:

| Area | Status |
|---|---|
| Auth (register/login/JWT), per-user data isolation | ✅ Done, tested |
| Document upload + validation (type/size) | ✅ Done, tested |
| Hand-built ingestion pipeline (loaders → chunking → embeddings → FAISS → FTS5) | ✅ Done |
| Hybrid retrieval (semantic + keyword, weighted merge) | ✅ Done, unit tested |
| Citation-grounded chat, with a free extractive fallback | ✅ Done |
| Multi-document chat | ✅ Done |
| Chat history | ✅ Done |
| Dashboard, real (non-fabricated) analytics | ✅ Done |
| Docker Compose (Postgres + backend + frontend) | ✅ Written, backend verified to boot; see caveats below |
| Retrieval evaluation harness | ✅ Built; dataset starts **empty** — fill it with your own questions |
| Document Summary page | ❌ Not built — no backend endpoint yet |
| Document Comparison page | ❌ Not built |
| Study Assistant (flashcards/MCQs) | ❌ Not built |
| Document Viewer (PDF page navigation, in-page highlighting) | ❌ Not built — documents can be uploaded/deleted/chatted with, but not previewed inline |
| OCR for scanned PDFs | ❌ Not built (fails clearly instead of silently returning nothing) |
| Frontend automated tests | ❌ Not built (backend has 26 automated tests) |

Sections 6–14 of the original spec are only partially realized: the pieces
that make the RAG pipeline and auth genuinely work are done and tested;
the extra productivity pages (summary/compare/study) were the first thing
cut when time ran out, in line with the spec's own instruction not to
fake a feature or ship a dead button.

## Quick start (local, no Docker)

**Backend:**
```bash
cd backend
python -m venv venv && source venv/bin/activate   # Windows: venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env                              # edit SECRET_KEY at minimum
uvicorn app.main:app --reload
```
API docs at `http://localhost:8000/docs` (FastAPI's automatic OpenAPI UI).

**Frontend:**
```bash
cd frontend
npm install
cp .env.example .env
npm run dev
```

Everytime : docker compose up --build
App at `http://localhost:5173`.

First document upload will download the embedding model
(`sentence-transformers/all-MiniLM-L6-v2`, ~90MB) from Hugging Face — this
needs internet access once; after that it's cached locally and fully
offline.

## Quick start (Docker)

```bash
docker compose up --build
```
This starts Postgres, the backend (against Postgres, not SQLite), and the
frontend. Set `GROQ_API_KEY` and `SECRET_KEY` as environment variables or
in a `.env` file at the repo root first (see `backend/.env.example` for
what they mean). **Caveat:** I wrote and reviewed this Compose file
carefully but could not run `docker compose up` inside the sandbox this
project was built in (no Docker daemon available there) — please treat it
as reviewed-but-unverified and file an issue if something doesn't start.

## Environment variables

See `backend/.env.example` for the full list with explanations. The two
that matter most:
- `DATABASE_URL` — defaults to a local SQLite file, zero setup required.
- `GROQ_API_KEY` — optional. Without it, chat still works in **extractive
  mode**: real retrieved excerpts with citations, no LLM-generated prose.
  Get a free key at https://console.groq.com if you want generated answers.

## Testing

```bash
cd backend
pytest -v
```
26 tests pass, covering chunking, hybrid-search score merging, citation
mapping, prompt-injection defense, document loaders, and full API flows
(auth, upload validation, cross-user isolation). One test needs to
download the embedding model and is skipped (not failed) if there's no
internet access — see [`docs/SETUP.md`](docs/SETUP.md) for details.

## Documentation

- [`docs/SETUP.md`](docs/SETUP.md) — detailed local + Docker setup, troubleshooting
- [`docs/ARCHITECTURE.md`](docs/ARCHITECTURE.md) — system design, what was preserved/rebuilt from the old app
- [`docs/ML_EXPLANATION.md`](docs/ML_EXPLANATION.md) — embeddings, hybrid search, RAG, evaluation explained simply
- [`docs/API_DOCUMENTATION.md`](docs/API_DOCUMENTATION.md) — every endpoint, with examples
- [`docs/INTERVIEW_PREPARATION.md`](docs/INTERVIEW_PREPARATION.md) — Q&A matched to what's actually implemented
- `backend/evaluation/README.md` — how to build a real retrieval evaluation dataset

## Tech stack

Backend: Python, FastAPI, SQLAlchemy, Pydantic, PyMuPDF, python-docx,
pandas, sentence-transformers, FAISS, SQLite FTS5, Groq.
Frontend: React, Vite, Tailwind CSS, React Router.
Database: SQLite (dev) / PostgreSQL (production, via `DATABASE_URL`).
Deployment: Docker, Docker Compose.

## Known limitations

- No OCR: scanned PDFs with no text layer fail with a clear error rather
  than silently returning nothing.
- DOCX has no real page concept (`python-docx` doesn't expose pagination),
  so DOCX citations always say "page 1" — documented, not hidden.
- Document processing runs synchronously in the upload request. Fine for
  a student project's file sizes; a production system would move this to
  a background job queue (Celery/RQ) so uploads return instantly.
- Hybrid search weights (0.7 semantic / 0.3 keyword) are the paper's
  suggested starting point, not something tuned against real data yet —
  `backend/evaluation/` is where you'd do that tuning.
- No reranking model — the spec lists this as optional, and it was cut
  along with the productivity pages above.

## License

MIT — see `LICENSE`.
