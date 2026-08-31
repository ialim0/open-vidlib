"""
/chat — basic video Q&A using the Mistral RAG pipeline.

Note: the richer agent-chat endpoint (with semantic search, dubbing routing,
and structured responses) lives in mistral_endpoints.py.
This endpoint is kept for compatibility and simpler integrations.
"""
import logging
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models.video import Video
from app.models.transcript import Transcript
from app.models.chat import VideoChatMessage
from app.schemas.chat import (
    VideoChatRequest,
    VideoChatResponse,
    ConversationHistoryResponse,
    ChatMessageItem,
)
from app.services.rag_qa_service import ask_video_question

router = APIRouter()
logger = logging.getLogger(__name__)


@router.post(
    "/video/{video_id}",
    response_model=VideoChatResponse,
    summary="Ask Coumba a question about a video",
)
async def chat_with_video(
    video_id: str,
    req: VideoChatRequest,
    db: Session = Depends(get_db),
):
    """
    Ask a question about a video. Coumba retrieves relevant transcript
    segments and returns a grounded answer with [MM:SS] timestamp citations.

    For richer responses (search results, dubbing, intent routing) use
    POST /videos/{id}/agent-chat instead.
    """
    video = db.query(Video).filter(Video.id == video_id).first()
    if not video:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Video '{video_id}' not found",
        )

    result = ask_video_question(
        video_id=video_id,
        question=req.message,
        db=db,
        session_id=req.session_id or "default",
    )
    answer_text = result.get("answer", "I could not find an answer in this video.")

    # Persist to simple chat history table
    record = VideoChatMessage(
        video_id=video_id,
        session_id=req.session_id,
        user_message=req.message,
        bot_response=answer_text,
        is_relevant=True,
        timestamp=datetime.now(timezone.utc),
    )
    db.add(record)
    db.commit()

    return VideoChatResponse(
        answer=answer_text,
        is_relevant=True,
        session_id=req.session_id,
        timestamp=record.timestamp,
    )


@router.get(
    "/video/{video_id}/history/{session_id}",
    response_model=ConversationHistoryResponse,
    summary="Get chat history for a session",
)
def get_chat_history(
    video_id: str,
    session_id: str,
    db: Session = Depends(get_db),
):
    """Return chronological chat history for a video session."""
    records = (
        db.query(VideoChatMessage)
        .filter(
            VideoChatMessage.video_id == video_id,
            VideoChatMessage.session_id == session_id,
        )
        .order_by(VideoChatMessage.timestamp.asc())
        .all()
    )

    messages = []
    for r in records:
        messages.append(ChatMessageItem(role="user", content=r.user_message, timestamp=r.timestamp))
        messages.append(ChatMessageItem(role="assistant", content=r.bot_response, timestamp=r.timestamp))

    return ConversationHistoryResponse(
        video_id=video_id,
        session_id=session_id,
        messages=messages,
    )
