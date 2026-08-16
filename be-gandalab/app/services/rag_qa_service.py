import logging
from sqlalchemy.orm import Session
from app.core.config import settings
from app.core.mistral_client import get_mistral_client, LLM_MODEL
from app.services.search_service import search_video
from app.models.qa_session import QASession

logger = logging.getLogger(__name__)

def ask_video_question(video_id: str, question: str, db: Session, session_id: str = "default-session") -> dict:
    # 1. Retrieve top-k chunks
    contexts = search_video(video_id, question, db, top_k=4)

    # 2. Format context with timestamps
    context_block = "\n".join([
        f"[{int(c['start_time']//60):02d}:{int(c['start_time']%60):02d}] {c['text']}"
        for c in contexts
    ])

    system_prompt = """You are Coumba, an intelligent and encouraging educational video research assistant for GandaLab.
Answer using ONLY the provided transcript context.
Cite every claim with a timestamp in [MM:SS] format.
Use helpful analogies when explaining complex concepts.
If the answer is not in the context, say: "The video doesn't mention this topic."
Be concise, clear, and factual."""

    user_prompt = f"""Context:
{context_block if context_block else "No video transcript available."}

Question: {question}
Answer:"""

    answer_text = ""
    client = get_mistral_client()

    if client and settings.MISTRAL_API_KEY:
        try:
            response = client.chat.complete(
                model=LLM_MODEL,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=0.1
            )
            answer_text = response.choices[0].message.content
        except Exception as e:
            logger.error(f"Mistral chat completion error: {e}")
            answer_text = f"Coumba AI: According to the video context [{int(contexts[0]['start_time']//60):02d}:{int(contexts[0]['start_time']%60):02d}], {contexts[0]['text'][:200]}..." if contexts else "Coumba AI: I could not find information regarding this question in the lesson."
    else:
        # Grounded fallback response using top context
        if contexts:
            top = contexts[0]
            mm = int(top['start_time'] // 60)
            ss = int(top['start_time'] % 60)
            answer_text = f"According to the video [{mm:02d}:{ss:02d}], {top['text'][:250]}..."
        else:
            answer_text = "The video transcript does not contain information to answer this question."

    # Record conversation in QA Session
    qa_record = db.query(QASession).filter(
        QASession.video_id == video_id,
        QASession.session_id == session_id
    ).first()

    if not qa_record:
        qa_record = QASession(
            video_id=video_id,
            session_id=session_id,
            messages=[]
        )
        db.add(qa_record)

    msgs = list(qa_record.messages or [])
    msgs.append({"role": "user", "content": question})
    msgs.append({"role": "assistant", "content": answer_text})
    qa_record.messages = msgs
    db.commit()

    return {
        "answer": answer_text,
        "sources": contexts,
        "question": question,
        "video_id": video_id
    }
