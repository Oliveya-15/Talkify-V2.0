"""
Ties retrieval + prompt construction + the Groq LLM + citation
persistence together into "ask a question, get a grounded answer".

Free-fallback behavior (per the spec's cost requirements): if no
GROQ_API_KEY is configured, or the Groq call fails, Talkify does not
just error out — it falls back to an *extractive* answer: the raw
top-ranked excerpt(s) with citations, no generation. This keeps the
retrieval half of the product fully testable and usable with zero
API cost, and degrades gracefully instead of breaking.
"""
from __future__ import annotations

import logging

from sqlalchemy.orm import Session

from app.config import settings
from app.models.conversation import Conversation, Message, MessageSource
from app.rag import citations as citations_module
from app.rag import prompt_builder
from app.services import retrieval_service

logger = logging.getLogger("talkify.chat")


def _call_groq(messages: list[dict]) -> str | None:
    if not settings.GROQ_API_KEY:
        logger.info("No GROQ_API_KEY configured — using extractive fallback.")
        return None
    try:
        from groq import Groq
        client = Groq(api_key=settings.GROQ_API_KEY)
        completion = client.chat.completions.create(
            model=settings.GROQ_MODEL,
            messages=messages,
            temperature=0.2,
            max_tokens=1024,
        )
        return completion.choices[0].message.content
    except Exception as e:  # noqa: BLE001 - any API failure triggers the extractive fallback
        # This is the single most important log line for diagnosing "why do
        # I only ever get the fallback text" — a deprecated/renamed model ID,
        # an invalid key, or a rate limit will show up here with the real
        # reason instead of failing silently.
        logger.warning("Groq call failed, falling back to extractive mode: %s", e)
        return None


def _extractive_fallback(excerpts: list[dict]) -> str:
    if not excerpts:
        return (
            "I couldn't find anything in the selected documents that answers this. "
            "Try rephrasing the question, or select a different document."
        )
    lines = ["Here's what your documents say, in the most relevant order:\n"]
    for e in excerpts:
        quote = e["text"].strip().replace("\n", " ")
        if len(quote) > 320:
            quote = quote[:320].rsplit(" ", 1)[0] + "…"
        lines.append(f'**[{e["index"]}] {e["source"]}, page {e["page"]}**\n> {quote}\n')
    return "\n".join(lines)


def _recent_history(conversation: Conversation, limit: int = 6) -> list[dict]:
    messages = sorted(conversation.messages, key=lambda m: m.created_at)[-limit:]
    return [{"role": m.role, "content": m.content} for m in messages]


def ask_question(db: Session, conversation: Conversation, question: str) -> Message:
    document_ids = (conversation.document_ids or "").split(",")
    document_ids = [d for d in document_ids if d]

    retrieved = retrieval_service.retrieve(db, document_ids, question)
    excerpts = citations_module.excerpts_for_prompt(retrieved)

    history = _recent_history(conversation)
    messages = prompt_builder.build_messages(question, excerpts, chat_history=history)

    answer = _call_groq(messages)
    used_fallback = answer is None
    if used_fallback:
        answer = _extractive_fallback(excerpts)

    citations = citations_module.build_citations(retrieved)

    assistant_message = Message(conversation_id=conversation.id, role="assistant", content=answer)
    db.add(assistant_message)
    db.commit()
    db.refresh(assistant_message)

    source_rows = [
        MessageSource(
            message_id=assistant_message.id,
            chunk_id=c.chunk_id,
            relevance_score=c.relevance_score,
            citation_order=c.index,
        )
        for c in citations
    ]
    db.add_all(source_rows)
    db.commit()

    # attach for the API response (not persisted on the ORM object itself)
    assistant_message.citation_data = [
        {
            "index": c.index, "document_id": c.document_id, "source_name": c.source_name,
            "page": c.page, "excerpt": c.excerpt, "relevance_score": c.relevance_score,
        }
        for c in citations
    ]
    return assistant_message
