import logging
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.database import get_db
from app.core.mistral_client import get_mistral_client, LLM_MODEL
from app.models.video import Video
from app.models.flashcard import Flashcard
from app.models.transcript import Transcript
from app.schemas.flashcard import FlashcardResponse, FlashcardCreate, FlashcardGenerateRequest

router = APIRouter()
logger = logging.getLogger(__name__)


@router.get(
    "/video/{video_id}",
    response_model=List[FlashcardResponse],
    summary="Get flashcards for a video",
)
def get_flashcards(
    video_id: str,
    lang: Optional[str] = Query(None, description="Language filter — en, fr, wo, ff, bm"),
    db: Session = Depends(get_db),
):
    """Return quiz flashcards stored for a video, optionally filtered by language."""
    query = db.query(Flashcard).filter(Flashcard.video_id == video_id)
    if lang:
        query = query.filter(Flashcard.language == lang)
    return query.all()


@router.post(
    "/video/{video_id}/generate",
    response_model=List[FlashcardResponse],
    summary="Generate flashcards from the video transcript (Mistral)",
)
async def generate_flashcards(
    video_id: str,
    req: FlashcardGenerateRequest,
    db: Session = Depends(get_db),
):
    """
    Generate {count} multiple-choice flashcards using the video transcript and
    mistral-large-latest. Returns a graceful fallback if no API key is set.
    """
    video = db.query(Video).filter(Video.id == video_id).first()
    if not video:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Video '{video_id}' not found",
        )

    transcript_obj = (
        db.query(Transcript)
        .filter(Transcript.video_id == video_id, Transcript.language == req.language)
        .first()
        or db.query(Transcript).filter(Transcript.video_id == video_id).first()
    )
    transcript_text = transcript_obj.full_text if transcript_obj else ""

    raw_cards = _generate_with_mistral(transcript_text, req.language, req.count)

    created: List[Flashcard] = []
    for card in raw_cards:
        fc = Flashcard(
            video_id=video_id,
            language=req.language,
            question=card.get("question", ""),
            options=card.get("options", []),
            correct_option=card.get("correct_option", 0),
            source=card.get("source", ""),
        )
        db.add(fc)
        created.append(fc)

    db.commit()
    for fc in created:
        db.refresh(fc)

    return created


def _generate_with_mistral(transcript: str, language: str, count: int) -> list:
    """Call the configured LLM to produce flashcards. Falls back to one stub card."""
    import json
    import re
    from app.core.llm_client import get_llm_model

    client = get_mistral_client()
    if not client:
        return [
            {
                "question": "What is the main concept introduced in this video?",
                "options": ["Observation and experimentation", "Memorisation", "Guessing"],
                "correct_option": 0,
                "source": "[00:10]",
            }
        ]

    prompt = f"""You are an expert STEM educator. Generate exactly {count} multiple-choice quiz questions based on the transcript below.

Rules:
- Each question must be grounded in the transcript.
- Provide exactly 3 options per question (1 correct, 2 plausible distractors).
- Include a source citation with a timestamp from the transcript (e.g. "[01:30]").
- Return ONLY valid JSON — no markdown, no prose.

Transcript:
{transcript[:18000] if transcript else "No transcript available."}

Return format:
{{
  "flashcards": [
    {{
      "question": "...",
      "options": ["A", "B", "C"],
      "correct_option": 0,
      "source": "[MM:SS]"
    }}
  ]
}}"""

    try:
        response = client.chat.complete(
            model=get_llm_model(),
            messages=[{"role": "user", "content": prompt}],
            temperature=0.3,
        )
        text = response.choices[0].message.content
        match = re.search(r"\{[\s\S]*\}", text)
        if match:
            return json.loads(match.group(0)).get("flashcards", [])
    except Exception as exc:
        logger.error("Flashcard generation failed: %s", exc)

    return []
