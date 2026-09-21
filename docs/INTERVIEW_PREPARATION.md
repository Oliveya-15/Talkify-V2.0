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
   - `embeddings.py` embeds every chunk with `all-MiniLM-L6-v2`.
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

### Why sentence-transformers + FAISS instead of a hosted embedding/vector DB API?

Cost and simplicity for a student project: both run entirely locally on
CPU, no per-request billing, no external service dependency once the
model is cached. FAISS's `IndexFlatIP` is exact (not approximate), which
is both simpler to reason about and fast enough at the scale of a single
document's chunks.

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
- Document processing is synchronous — fine for small student-project
  files, but a production system would use a background job queue so
  uploads return immediately.
- No reranking model, no OCR, no Summary/Compare/Study-assistant pages
  yet — cut for time, and explicitly listed as not-built in the README
  rather than faked with a dead button.

### What would you improve next?

In priority order: (1) a background task queue for ingestion so large
uploads don't block the request, (2) a real evaluation dataset with
measured numbers checked into the repo, (3) the Document Viewer with
inline page navigation and highlighting so a citation click actually
jumps to the right spot, (4) Summary and Study Assistant features, which
reuse the same retrieval pipeline with a different prompt.
