import logging
from sqlalchemy.orm import Session
from app.core.config import settings
from app.core.mistral_client import get_mistral_client, get_llm_model, LLM_MODEL
from app.services.search_service import search_video
from app.models.qa_session import QASession

logger = logging.getLogger(__name__)

def ask_video_question(video_id: str, question: str, db: Session, session_id: str = "default-session") -> dict:
    # Include a small amount of conversation history for follow-up questions.
    qa_record = db.query(QASession).filter(
        QASession.video_id == video_id,
        QASession.session_id == session_id,
    ).first()
    previous_user_questions = [
        message.get("content", "")
        for message in (qa_record.messages[-6:] if qa_record else [])
        if message.get("role") == "user"
    ]
    retrieval_query = " ".join(previous_user_questions[-2:] + [question]).strip()

    # Retrieve more candidates, then deduplicate and cap the evidence window.
    raw_contexts = search_video(video_id, retrieval_query, db, top_k=8)
    contexts = []
    seen_text = set()
    context_chars = 0
    for context in raw_contexts:
        normalized = " ".join(context["text"].lower().split())
        if normalized in seen_text:
            continue
        block_size = len(context["text"]) + 32
        if contexts and context_chars + block_size > 6000:
            break
        seen_text.add(normalized)
        contexts.append(context)
        context_chars += block_size

    context_lines = []
    for item in contexts:
        sentences = item.get("sentences") or []
        if sentences:
            for s in sentences:
                start_sec = float(s.get("start", 0))
                context_lines.append(f"[{int(start_sec // 60):02d}:{int(start_sec % 60):02d}] {s.get('text', '')}")
        else:
            context_lines.append(f"[{int(item['start_time'] // 60):02d}:{int(item['start_time'] % 60):02d}] {item['text']}")

    context_block = "\n".join(context_lines)

    system_prompt = """You are Coumba, an encouraging educational tutor for Open VidLib.
Use only the supplied transcript evidence to answer the learner's question.
If the learner asks in or requests a specific language (including Wolof, Pulaar/Fulfulde, Bambara, French, or English), formulate your answer in that requested language.
Every factual statement about the lesson must include a timestamp in [MM:SS] format from the evidence.
Explain concepts clearly with a short analogy when useful, but label analogies as explanations rather than transcript facts.
Do not invent details, sources, timestamps, or facts that are absent from the evidence.
If the evidence is insufficient, say exactly: "The video does not provide enough information to answer that."""

    user_prompt = f"""Transcript evidence:
{context_block if context_block else "No relevant transcript evidence was found."}

Learner question: {question}
Answer with the strongest evidence first:"""

    answer_text = ""
    client = get_mistral_client()

    if client:
        try:
            response = client.chat.complete(
                model=get_llm_model(),
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt},
                ],
                temperature=0.05,
            )
            answer_text = response.choices[0].message.content or "The video does not provide enough information to answer that."
        except Exception as exc:
            logger.error("LLM chat completion error: %s", exc)
            answer_text = (
                f"According to the video [{int(contexts[0]['start_time'] // 60):02d}:{int(contexts[0]['start_time'] % 60):02d}], "
                f"{contexts[0]['text'][:250]}..."
                if contexts else "The video does not provide enough information to answer that."
            )
    elif contexts:
        top = contexts[0]
        answer_text = f"According to the video [{int(top['start_time'] // 60):02d}:{int(top['start_time'] % 60):02d}], {top['text'][:250]}..."
    else:
        answer_text = "The video transcript does not contain information to answer this question."

    try:
        if not qa_record:
            qa_record = QASession(video_id=video_id, session_id=session_id, messages=[])
            db.add(qa_record)
        messages = list(qa_record.messages or [])
        messages.extend([
            {"role": "user", "content": question},
            {"role": "assistant", "content": answer_text},
        ])
        qa_record.messages = messages[-20:]
        db.commit()
    except Exception as exc:
        db.rollback()
        logger.warning("Could not persist QA session: %s", exc)

    return {
        "answer": answer_text,
        "sources": contexts,
        "question": question,
        "video_id": video_id,
    }
