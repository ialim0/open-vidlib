import os
import logging
import tempfile
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Form, UploadFile, File, Query, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models.video import Video
from app.models.transcript import Transcript
from app.schemas.transcript import (
    TranscriptResponse,
    TranscriptBase,
    WhisperTranscriptResponse,
)

router = APIRouter()
logger = logging.getLogger(__name__)


@router.get(
    "/video/{video_id}",
    response_model=List[TranscriptResponse],
    summary="Get transcripts for a video",
)
def get_transcripts_for_video(
    video_id: str,
    lang: Optional[str] = Query(None, description="Language code — en, fr, wo, ff, bm"),
    db: Session = Depends(get_db),
):
    """Return all stored transcripts for a video, optionally filtered by language."""
    query = db.query(Transcript).filter(Transcript.video_id == video_id)
    if lang:
        query = query.filter(Transcript.language == lang)
    return query.all()


@router.post(
    "/video/{video_id}",
    response_model=TranscriptResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Add a transcript to a video",
)
def create_transcript(
    video_id: str,
    transcript_in: TranscriptBase,
    db: Session = Depends(get_db),
):
    """Store a word-level transcript for a video (language + words JSON)."""
    video = db.query(Video).filter(Video.id == video_id).first()
    if not video:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Video '{video_id}' not found",
        )

    record = Transcript(
        video_id=video_id,
        language=transcript_in.language,
        full_text=transcript_in.full_text,
        words=[w.dict() for w in transcript_in.words] if transcript_in.words else None,
        segments=[s.dict() for s in transcript_in.segments] if transcript_in.segments else None,
    )
    db.add(record)
    db.commit()
    db.refresh(record)
    return record


# ---------------------------------------------------------------------------
# Self-hosted ASR endpoints (roadmap — not yet implemented)
# These will use faster-whisper or the OpenAI Whisper API once configured.
# Tracked in: https://github.com/your-username/openvidlib/issues/XX
# ---------------------------------------------------------------------------

@router.post(
    "/transcribe/youtube",
    response_model=WhisperTranscriptResponse,
    summary="[Roadmap] Transcribe a YouTube URL",
)
async def transcribe_youtube(
    youtube_url: str = Form(..., description="Public YouTube URL"),
):
    """
    Download audio from YouTube and return word-level timestamps.

    Not yet implemented. Planned approach:
    1. Download audio with yt-dlp.
    2. Transcribe with faster-whisper (local) or the OpenAI Whisper API.
    3. Return word-level JSON ready to store via POST /transcripts/video/{id}.
    """
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail=(
            "Self-hosted ASR transcription is on the roadmap. "
            "For now, generate a transcript with any Whisper tool and POST it to "
            "/transcripts/video/{id}."
        ),
    )


@router.post(
    "/transcribe/audio",
    response_model=WhisperTranscriptResponse,
    summary="[Roadmap] Transcribe an uploaded audio file",
)
async def transcribe_audio_file(
    file: UploadFile = File(...),
):
    """
    Accept an audio file and return word-level timestamps.

    Not yet implemented — see /transcribe/youtube for details.
    """
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail="Audio upload transcription is on the roadmap.",
    )
