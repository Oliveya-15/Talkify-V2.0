# Setup Guide

## Required software

- Python 3.11+ (built and tested on 3.12)
- Node.js 18+ (built and tested on 22)
- Git
- Optional: Docker + Docker Compose
- Optional: a free Groq API key (https://console.groq.com) for LLM-generated
  answers — the app works without one, in extractive fallback mode.

## 1. Backend — local (SQLite, zero setup)

```bash
cd backend
python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env
```

Open `.env` and set at minimum:
```
SECRET_KEY=<run: python -c "import secrets; print(secrets.token_hex(32))">
GEMINI_API_KEY=<free key, no card: https://aistudio.google.com/apikey>
```
Everything else has a sensible default (SQLite database, extractive-only
chat with no `GROQ_API_KEY`). `GEMINI_API_KEY` is the one variable that
isn't optional — document processing calls the Gemini embedding API for
every upload, and there's no local/offline fallback for that specific
step (there is one for chat generation — see `GROQ_API_KEY` below).

```bash
uvicorn app.main:app --reload
```

Visit `http://localhost:8000/docs` for the interactive API docs (FastAPI
generates this automatically from the route type hints — nothing extra
to write).

## 2. Backend — with PostgreSQL instead of SQLite

```bash
# create a local Postgres database, e.g.:
createdb talkify
```
In `.env`:
```
DATABASE_URL=postgresql+psycopg2://<user>:<password>@localhost:5432/talkify
```
Then either let the app create tables automatically on first run
(`Base.metadata.create_all`, fine for development), or run Alembic
migrations properly:
```bash
alembic upgrade head
```

## 3. Frontend

```bash
cd frontend
npm install
cp .env.example .env      # VITE_API_URL should point at your backend
npm run dev
```
Visit `http://localhost:5173`.

## 4. Docker Compose (both services + Postgres)

```bash
# from the repo root
cp backend/.env.example .env       # docker-compose.yml reads SECRET_KEY / GEMINI_API_KEY / GROQ_API_KEY from here
docker compose up --build
```
- Backend: `http://localhost:8000`
- Frontend: `http://localhost:5173`
- Postgres: `localhost:5432` (user/password/db all `talkify`, see `docker-compose.yml`)

> **Verification note:** this Compose file was written and reviewed
> carefully (correct depends_on/healthcheck ordering, environment
> variables, volumes) but the sandbox this project was built in had no
> Docker daemon, so `docker compose up` itself could not be run end-to-end
> here. Please treat it as reviewed-but-unverified on first use.

## 5. Free production deployment (Vercel + Render + Neon)

This is the exact path the live deployment at
[talkify-v2-0.vercel.app](https://talkify-v2-0.vercel.app) uses — zero
cost, no credit card anywhere in the chain.

**Get two free API keys first:**
- Gemini (required): [aistudio.google.com/apikey](https://aistudio.google.com/apikey) — sign in with any Google account, no card.
- Groq (optional): [console.groq.com/keys](https://console.groq.com/keys) — leave unset to run chat in extractive-fallback mode.

**Generate a production secret:**
```bash
python -c "import secrets; print(secrets.token_hex(32))"
```

**Database — Neon:**
1. [neon.tech](https://neon.tech) → sign in → **New Project**.
2. Copy the connection string, then change its prefix from `postgresql://`
   to `postgresql+psycopg2://`, keeping `?sslmode=require` intact. Result:
   ```
   postgresql+psycopg2://<user>:<password>@<host>.neon.tech/<db>?sslmode=require
   ```
3. No manual migration needed — `Base.metadata.create_all()` runs on the
   app's startup hook and creates every table on first boot.

**Backend — Render:**
1. [render.com](https://render.com) → sign in with GitHub (no card for free tier).
2. **New +** → **Web Service** → connect this repo.
3. **Root Directory**: `backend`. **Runtime**: Docker (auto-detected). **Instance Type**: Free.
4. Environment variables:

   | Key | Value |
   |---|---|
   | `DATABASE_URL` | the Neon string above |
   | `SECRET_KEY` | the generated secret above |
   | `GEMINI_API_KEY` | your Gemini key |
   | `GROQ_API_KEY` | your Groq key (or omit entirely) |
   | `GROQ_MODEL` | `openai/gpt-oss-20b` |
   | `CORS_ORIGINS` | `["http://localhost:5173"]` (revisit after the frontend is deployed) |

   `CORS_ORIGINS` must be valid JSON — square brackets and double quotes
   exactly as shown, or the app crashes on startup with a config
   validation error.
5. **Create Web Service**. Build takes a few minutes; watch the **Logs** tab.
6. Verify before moving on:
   ```bash
   curl https://<your-service>.onrender.com/api/health
   curl -X POST https://<your-service>.onrender.com/api/auth/register \
     -H "Content-Type: application/json" \
     -d '{"name":"Test","email":"test@example.com","password":"password123"}'
   ```
   Confirming this works standalone, before touching the frontend, isolates
   which half of the stack any later problem is in.

**Frontend — Vercel:**
1. [vercel.com](https://vercel.com) → import this repo.
2. **Root Directory**: `frontend`. **Framework**: Vite.
3. Environment variable: `VITE_API_URL` = your Render URL from above.
4. Deploy.

**Connect them:** back on Render, update `CORS_ORIGINS` to your real Vercel
URL (`["https://your-app.vercel.app"]`) and save — this triggers an
automatic redeploy.

**Known trade-off:** Render's free tier has no persistent disk. Uploaded
files and their FAISS/FTS5 indexes don't survive a redeploy or a long
idle-triggered restart — document metadata in Postgres does. Fine for a
live demo; see the README's Roadmap for the planned fix.

## 6. Running tests

```bash
cd backend
pytest -v
```

Expected: 40+ passed. One test (`test_txt_upload_processes_successfully`)
needs live internet access to the Gemini API on first run; if that's not
available it will report **skipped**, not failed, with an explicit
reason printed.

## Troubleshooting

**Login/register returns 404 "Not Found" even though the server starts fine.**
This has a specific, confirmed cause: an unpinned or mismatched FastAPI
version. While building this project, running a bare `pip install fastapi`
(instead of `pip install -r requirements.txt`) pulled a much newer FastAPI
release with different internal routing behavior — under it, routes were
missing entirely from the app, producing exactly this symptom (a real
`{"detail":"Not Found"}` response from a server that otherwise starts and
logs "Application startup complete" normally). To confirm and fix:
```bash
cd backend
source venv/bin/activate          # make sure you're in the venv
pip show fastapi                  # must say exactly 0.115.0
# if it says anything else:
pip install fastapi==0.115.0 starlette==0.38.6
```
Then restart `uvicorn` fully (stop it, don't rely on `--reload` picking
this up) and try again. To check without guessing, run the self-check
script from the repo root while the backend is running:
```bash
pip install -r scripts/requirements.txt
python scripts/verify_setup.py
```
It talks to your backend directly (no browser, no frontend, no CORS) and
tells you exactly which layer is broken — including this specific check.

**Groq errors / no LLM answers / always seeing the "here's what your
documents say" fallback text** — as of late 2026, Groq moved
`llama-3.1-8b-instant` to an Enterprise/contact-sales-only tier; calling
it with a normal developer API key fails, and the app used to swallow
that failure silently. Two things fix this: (1) `GROQ_MODEL` now
defaults to `openai/gpt-oss-20b`, which is on the standard developer
tier — if you set a custom model in `.env`, check
https://console.groq.com/docs/models for current availability; (2) Groq
failures are now logged (`logger.warning` in `chat_service.py`) — check
your `uvicorn` terminal output for a line like `Groq call failed,
falling back to extractive mode: ...` which tells you the *actual* reason
(bad key, decommissioned model, rate limit, etc.) instead of guessing.
Leaving `GROQ_API_KEY` blank entirely is still a supported, deliberate
choice — the fallback text is meant to be a clean, readable list of
retrieved excerpts either way, not an error message.

**Upload feels like it freezes the page** — this was true in earlier
versions: the upload request didn't return until embedding finished.
Uploads now return immediately (status `uploaded`), and processing
(chunking, embedding, indexing) runs in a background task; the frontend
polls `GET /api/documents/{id}` every ~1.2s and updates the status badge
live (`uploaded` → `processing` → `completed`/`failed`). If you're
calling the API directly rather than through the frontend, don't expect
`processing_status: "completed"` in the upload response itself anymore —
poll for it.

**"No such table: users"** — the app creates tables on startup
(`app/main.py`'s `on_startup` hook). If you're calling the app
programmatically (not through `uvicorn`), make sure the app's startup
event actually runs, or call `Base.metadata.create_all(bind=engine)`
yourself first.

**bcrypt / passlib error about 72-byte passwords** — this is a known
incompatibility between `passlib==1.7.4` and `bcrypt>=4.1`. The pinned
`requirements.txt` already fixes this with `bcrypt==4.0.1`; if you see
this error you likely have a newer bcrypt installed some other way —
reinstall with `pip install "bcrypt==4.0.1"`.

**Documents stuck on "processing" forever, no error anywhere** — this had
a specific, confirmed cause in production: Neon's pooled Postgres
connection can silently close during the real 10-60+ second gap between
marking a document "processing" and finishing embedding, and the
resulting exception wasn't being caught anywhere. Fixed with
`pool_pre_ping`/`pool_recycle` in `database.py` and a background-task
safety net (`api/routes/documents.py::_mark_failed`) that guarantees a
document ends up in a terminal state (`completed` or `failed`) with a
real error message. If you still see a document stuck, check Render's
**Logs** tab for a `talkify.documents` logger entry — the real reason
will be there now instead of nowhere.

**Upload fails immediately with a `GEMINI_API_KEY is not configured`
error** — exactly what it says: set `GEMINI_API_KEY` in your environment.
There's no local embedding fallback (unlike chat generation, which
degrades gracefully without `GROQ_API_KEY`) — see
`docs/ML_EXPLANATION.md`'s Embeddings section for why.

**Upload fails with a Gemini API error mentioning 429 or rate limits** —
free-tier rate limit. `embeddings.py` already retries transient failures
with backoff; a persistent 429 means you're uploading unusually large
documents unusually fast for a free key.

**Backend gets OOM-killed / container restarts on every upload** — this
was a real, confirmed issue with an earlier version of this project that
ran embeddings locally via PyTorch, which needs 200MB-1GB+ of RAM
independent of model size — more than free hosting tiers' ~512MB limit
allows. It's resolved architecturally now (embeddings call the Gemini
API instead of loading a local model — see `docs/INTERVIEW_PREPARATION.md`
for the full story), so this shouldn't recur unless you've reintroduced
a local model yourself.

**CORS errors in the browser console** — make sure `CORS_ORIGINS` in the
backend's `.env` includes your frontend's actual URL (default
`http://localhost:5173`).

**Groq errors / no LLM answers** — leaving `GROQ_API_KEY` blank is fine;
the app falls back to showing the raw retrieved excerpts with citations
instead of an error.
