# Retrieval evaluation dataset

`dataset.json` starts empty on purpose — a fabricated evaluation dataset
would be worse than no dataset at all (see docs/ML_EXPLANATION.md).

## How to fill it in

1. Register a user and upload 2-3 real documents through the running app.
2. Open each document (or its extracted chunks in the DB) and pick 15-25
   questions where you, a human, can point at the exact page that answers
   the question.
3. Add one JSON object per question to `dataset.json`:

```json
{
  "question": "What is supervised learning?",
  "document_ids": ["<uuid of the document(s) this chat is scoped to>"],
  "expected_document_id": "<uuid of the document containing the answer>",
  "expected_page": 4,
  "notes": "Defined in the first paragraph of section 2."
}
```

4. Run:

```bash
cd backend
python -m evaluation.retrieval_metrics
```

This prints `recall_at_5` (fraction of questions where the right page was
in the top 5 retrieved chunks) and mean reciprocal rank, computed from
your real database and real FAISS indexes — not simulated numbers.
