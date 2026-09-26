# Interview Preparation

Answers here are written to match what's actually in this repo — you
should be able to open the referenced file and point at the exact lines
if asked to go deeper.

### What is RAG, and why use it instead of just prompting the LLM directly?

RAG (Retrieval-Augmented Generation) retrieves relevant text from an
external source — here, your uploaded documents — and includes it in the
prompt before asking the LLM to answer. Without it, the LLM can only
answer from what it memorized during training, which might be outdated,
generic, or simply not about your specific document at all. With it, the
answer is grounded in text that's actually shown to the model, and you
can cite exactly which passage supports each claim.

### Walk me through what happens between upload and answer.

1. Upload hits `POST /api/documents`; `document_service.validate_upload`
   checks extension and size before anything touches disk.
2. The file is saved under a random UUID filename (never the original
   name — avoids path traversal), and a `Document` row is created with
   status `uploaded`.
3. `document_service.process_document` calls `rag.pipeline.ingest_document`:
   - `loaders.py` extracts text per-page (PyMuPDF/python-docx/pandas/stdlib).
   - `chunking.py` splits each page into ~1000-character overlapping chunks.
   - `embeddings.py` embeds every chunk via the Gemini embedding API
     (`gemini-embedding-001`, requested at 384 dimensions).
   - `vector_store.py` builds a FAISS index for that document.
   - `keyword_search.py` indexes the same chunks into SQLite FTS5.
4. `DocumentChunk` rows are saved, each with a `vector_ref` pointing at
   its row in the FAISS index — this is what makes retrieval traceable
   back to real text.
5. On `POST /api/chat/conversations/{id}/ask`, `retrieval_service.retrieve`
   runs semantic search (FAISS) and keyword search (FTS5) across the
   conversation's documents, `hybrid_search.merge_results` combines and
   ranks them, `citations.py` turns the top results into numbered
   citations, `prompt_builder.py` builds a messages array with system
   instructions, the numbered excerpts, and the question, and
   `chat_service._call_groq` (or the extractive fallback) produces the
   final answer.

### Why a hosted embedding API instead of a local model?

This wasn't the original design — Talkify originally ran
sentence-transformers locally via PyTorch, which is genuinely the more
commonly recommended approach for a project like this: free, no
external dependency, fully explainable. It's also what I'd default to
again on a server with normal memory. The problem showed up specifically
in deployment: PyTorch needs 200MB-1GB+ of resident memory just to run,
independent of which model is loaded into it, and every genuinely free,
card-free hosting tier in 2026 caps around 512MB. I spent real time
trying to make the local model fit — pinning thread counts, batching
encode calls, forcing garbage collection and `malloc_trim` after each
batch, switching to a much smaller model — and it still got OOM-killed
under real load. At that point the honest conclusion was that this was
an architectural mismatch, not a tuning problem, so I removed PyTorch
entirely and moved embedding generation to Google's Gemini API instead.
Measured result: backend memory dropped from an OOM-crashing 512MB+ to
about 147MB RSS (checked via `/proc/<pid>/status`, not guessed).
The trade-off, stated plainly: embeddings now need internet access and a
free API key, and there's no local fallback if that call fails — see
`docs/ML_EXPLANATION.md`'s Embeddings section for the full reasoning.

### Tell me about a hard bug you debugged in this project.

Three, actually, all found in the same deployment push, each with a
distinct root cause worth walking through separately:

**1. Auth routes 404ing despite the server starting normally.**
Symptom: `POST /api/auth/login` returned a real `404 {"detail":"Not
Found"}` — not a crash, not a timeout, an actual "this route doesn't
exist" response, even though the server logged "Application startup
complete." Root cause: I'd installed FastAPI with a bare `pip install
fastapi` at one point instead of the pinned `requirements.txt`, which
pulled a materially newer release with different internal router
registration behavior that silently dropped routes. Fix: pinned
`fastapi` and `starlette` together to exact versions, and wrote
`scripts/verify_setup.py`, which checks the installed FastAPI version by
name and confirms expected routes exist in the OpenAPI schema — so this
exact failure mode is caught immediately if it ever recurs, rather than
requiring another multi-hour debugging session.

**2. Documents stuck on "processing" forever, no error anywhere.**
Symptom: upload would succeed (`201 Created`), then the document would
just... never finish. No error in the frontend, nothing obviously wrong
in the backend logs. Root cause, once I actually reasoned through the
timing: there's a real gap — often 10-60+ seconds — between marking a
document `"processing"` and finishing embedding, during which the
background task does no database activity at all. Neon's pooled
connection endpoint (PgBouncer) can silently close an idle connection in
that window. SQLAlchemy had no way to detect this, so the *next* query
threw — and the deeper bug was that nothing caught that exception. It
escaped the background task silently, so the document's status was never
touched again. Fix: `pool_pre_ping=True` and `pool_recycle=280` in
`database.py` so a dead connection gets transparently replaced before
use, *and* wrapping the entire background task in a try/except that
guarantees the document ends up marked `failed` with a real message
(using a fresh connection, since the original one might be the broken
one) if anything goes wrong at all. The second fix matters independent
of the first: it means *any* future unexpected failure surfaces as a
clear error instead of an infinite spinner.

**3. The backend container getting OOM-killed on every upload.**
Covered above — worth naming here too because it's the most
consequential of the three: it wasn't fixable by tuning, only by
recognizing the architecture itself didn't fit the constraint and
changing it.

The pattern across all three: in each case the visible symptom (a 404, a
stuck spinner, a crashed container) was several steps removed from the
actual cause, and the fix that mattered wasn't just patching the
symptom — for #1 it was adding a version-pinning safeguard, for #2 it
was making failures loud instead of silent everywhere in the codebase,
not just this one call site, and for #3 it was accepting that the
original design decision needed to change rather than working around it
indefinitely.

### Why hybrid search instead of just semantic search?

Semantic search is very good at matching meaning ("how does attention
work" matching a passage about "assigning different weights to input
tokens") but can miss a question that hinges on one exact term it hasn't
seen much — a product name, a specific number, an acronym. Keyword
search catches exactly that case. Combining both (with normalized,
weighted scores — see `hybrid_search.py`) covers more question types
than either alone.

### How do you know the 0.7/0.3 weight split is right?

Honestly — I don't know that it's optimal; it's the starting point the
spec suggested, and I say so directly in the code's docstring and the
README. `backend/evaluation/retrieval_metrics.py` is built specifically
to let you measure recall@k and MRR against a real question set and then
try different weight combinations to see what actually improves it —
that's the intellectually honest answer, not "the weights are perfect."

### How are hallucinations reduced (not eliminated)?

The system prompt instructs the model to answer only from the provided
excerpts and say when there isn't enough evidence, rather than falling
back on general knowledge. Answers are grounded in retrieved text and
cited, so a wrong-but-fluent answer is at least checkable against the
cited source. None of this makes hallucination impossible — it's risk
reduction, not a guarantee, and the README and prompt itself say so.

### How do you defend against prompt injection?

Document content could contain something like "ignore previous
instructions." `prompt_builder.py` keeps three things in strictly
separate message roles/blocks: the fixed system instructions (never
influenced by document content), a clearly delimited "DOCUMENT EXCERPTS
(untrusted...)" block, and the user's actual question. The system prompt
explicitly tells the model that anything inside the excerpts block is
data to analyze, not instructions to follow. This is tested directly in
`tests/test_citations_and_prompts.py`.

### How is authentication implemented, and how do you know users can't see each other's data?

JWT tokens (`python-jose`), signed with a server-side `SECRET_KEY`,
containing the user ID as the subject. `app/core/deps.py::get_current_user`
decodes the token on every protected request. Every document/conversation
query in `api/routes/*.py` filters by `user_id == current_user.id`, and a
request for another user's resource returns `404` (not `403`, so
existence isn't leaked either). This is directly tested in
`tests/test_api.py::test_users_cannot_see_each_others_documents`.

### Why not just use LangChain's ConversationalRetrievalChain like the old app did?

That one call hides chunking, retrieval, and prompt construction inside
a framework abstraction — you can use it without understanding any of
those steps, which is fine for a demo but not for something I need to
explain and defend in an interview. Rebuilding chunking, hybrid
retrieval, prompt construction, and citation mapping as separate,
readable modules means I can point to the exact code for any of those
steps and explain a design decision, instead of saying "LangChain does
that part."

### Why not train an LLM (or fine-tune one) yourself?

Pretraining needs enormous compute and data that aren't realistic for a
student project; fine-tuning a useful model still needs curated data and
meaningful compute to do well. The actual engineering value here is in
the retrieval and system-design layer — deciding what evidence to show
the model and how — which is exactly what this project focuses on
instead.

### How is the system evaluated?

`backend/evaluation/retrieval_metrics.py` computes recall@k and mean
reciprocal rank against a manually verified question set
(`evaluation/dataset.json`) where a human has already identified the
correct source document/page for each question. The dataset ships empty
on purpose — filling it in with real questions about real uploaded
documents, and reporting the actual numbers that come out, is the honest
version of "this system is evaluated." (Contrast with just claiming an
accuracy percentage with nothing behind it.)

### What are the current limitations?

- No OCR — a scanned PDF with no text layer fails clearly rather than
  silently returning empty results.
- DOCX pagination doesn't really exist in `python-docx`, so DOCX
  citations always say "page 1" (documented, not hidden).
- Embeddings require internet access and a Gemini API key — there's no
  offline/local fallback for that specific step (there is one for LLM
  generation — see the extractive fallback above).
- No reranking model, no Summary/Compare/Study-assistant pages yet — cut
  for time, and explicitly listed as not-built in the README rather than
  faked with a dead button.
- Uploaded files and their FAISS/keyword indexes live on the backend's
  local disk, which is ephemeral on Render's free tier — they don't
  survive a redeploy or a long idle-triggered restart. Document
  metadata in Postgres persists fine; only the actual search index
  underneath it doesn't yet.

### What would you improve next?

In priority order: (1) move uploaded files and indexes into
Postgres-backed or object storage so they survive a redeploy — the one
remaining piece of the free-tier architecture that isn't fully durable,
(2) a real evaluation dataset with measured recall@k/MRR numbers checked
into the repo, (3) the Document Viewer with inline page navigation and
highlighting so a citation click actually jumps to the right spot, (4)
Summary and Study Assistant features, which reuse the same retrieval
pipeline with a different prompt.
