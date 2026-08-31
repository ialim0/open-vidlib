from fastapi import APIRouter, Depends, HTTPException, Query, status
from typing import Literal
from pathlib import Path
from threading import Lock
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.core.llm_client import get_llm_model, get_llm_provider
from app.models.video import Video
from app.models.audio_dub import AudioDub
from app.schemas.mistral_schemas import (
    IngestRequest, IngestResponse,
    SearchRequest, SearchResponse,
    RAGQuestionRequest, RAGAnswerResponse,
    DubbingRequest, DubbedTrackResponse,
    AgentChatRequest, AgentChatResponse
)
from app.services.ingest_service import chunk_and_embed
from app.services.search_service import search_video
from app.services.rag_qa_service import ask_video_question
from app.services.dubbing_service import create_dubbed_track, load_translated_captions, SUPPORTED_DUB_LANGUAGES
from app.services.agent_chat_baseline import route_user_intent_baseline
from app.services.agent_chat_loop import run_agent_loop
from app.services.orchestrator_service import run_orchestrated_agent
from app.core.mistral_client import LLM_MODEL

router = APIRouter()
_dubbing_lock = Lock()

@router.post("/{video_id}/ingest", response_model=IngestResponse, summary="Ingest & Embed Captions with mistral-embed")
def ingest_video_captions(
    video_id: str,
    payload: IngestRequest,
    db: Session = Depends(get_db)
):
    """
    Ingest captions: chunk ~500 chars with sentence awareness,
    embed with mistral-embed (1024-dim), and store in pgvector.
    """
    video = db.query(Video).filter(Video.id == video_id).first()
    if not video:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Video '{video_id}' not found")

    captions_data = [c.dict() for c in payload.captions]
    count = chunk_and_embed(video_id, captions_data, db, language=payload.language)

    return IngestResponse(
        video_id=video_id,
        chunks_created=count,
        message=f"Successfully ingested and embedded {count} chunks with mistral-embed"
    )

@router.post("/{video_id}/search", response_model=SearchResponse, summary="Semantic Search via pgvector")
def search_in_video(
    video_id: str,
    payload: SearchRequest,
    db: Session = Depends(get_db)
):
    """
    Query -> mistral-embed -> pgvector cosine similarity search
    Returns ranked timestamped segments with similarity scores.
    """
    video = db.query(Video).filter(Video.id == video_id).first()
    if not video:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Video '{video_id}' not found")

    results = search_video(video_id, payload.query, db, top_k=payload.top_k)
    return SearchResponse(
        video_id=video_id,
        query=payload.query,
        results=results
    )

@router.post("/{video_id}/ask", response_model=RAGAnswerResponse, summary="RAG Q&A with Mistral Large")
def ask_video_rag(
    video_id: str,
    payload: RAGQuestionRequest,
    db: Session = Depends(get_db)
):
    """
    RAG Q&A: Retrieve top-k chunks -> generate grounded answer
    with [MM:SS] timestamp citations using Mistral Large.
    """
    video = db.query(Video).filter(Video.id == video_id).first()
    if not video:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Video '{video_id}' not found")

    res = ask_video_question(video_id, payload.question, db, session_id=payload.session_id or "default-session")
    return RAGAnswerResponse(
        answer=res["answer"],
        sources=res["sources"],
        question=payload.question,
        video_id=video_id
    )

@router.post("/{video_id}/dub", response_model=DubbedTrackResponse, summary="Trigger Translation & Voxtral Audio Dubbing")
def dub_video(
    video_id: str,
    payload: DubbingRequest,
    db: Session = Depends(get_db)
):
    """
    Translate text with Mistral Large -> generate audio with Voxtral TTS
    -> store segments -> return synchronized audio dub track.
    """
    video = db.query(Video).filter(Video.id == video_id).first()
    if not video:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Video '{video_id}' not found")

    if payload.language.lower() not in SUPPORTED_DUB_LANGUAGES:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Dubbing is currently available only in English and French. Other languages are coming soon.")

    try:
        with _dubbing_lock:
            result = create_dubbed_track(video_id, payload.language, payload.voice_gender, db)
    except RuntimeError as exc:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=str(exc)) from exc
    return DubbedTrackResponse(**result)

@router.get("/{video_id}/dub/{lang}", response_model=DubbedTrackResponse, summary="Get Dubbed Audio Track")
def get_dubbed_track(
    video_id: str,
    lang: str,
    db: Session = Depends(get_db)
):
    """Retrieve ordered audio dub segments for video player synchronization."""
    dubs = db.query(AudioDub).filter(
        AudioDub.video_id == video_id,
        AudioDub.language == lang
    ).order_by(AudioDub.start_time.asc()).all()
    dubs = [
        dub for dub in dubs
        if Path(dub.audio_path.lstrip("/" )).exists()
        and Path(dub.audio_path.lstrip("/" )).stat().st_size > 1024
    ]

    translated_captions = load_translated_captions(video_id, lang)
    segments = [
        {
            "segment_id": d.segment_id,
            "audio_url": d.audio_path,
            "start": d.start_time,
            "end": d.end_time,
            "translated_text": translated_captions.get(d.segment_id)
        }
        for d in dubs
    ]

    return DubbedTrackResponse(
        video_id=video_id,
        language=lang,
        voice=dubs[0].voice_id if dubs else "neutral_female",
        status="completed" if dubs else "not_found",
        segments=segments
    )

@router.post("/{video_id}/agent-chat", response_model=AgentChatResponse, summary="Verified Multistep Agent (Mistral Tool Calling)")
def agent_chat(
    video_id: str,
    payload: AgentChatRequest,
    mode: Literal["loop", "baseline", "orchestrated"] = Query("loop"),
    db: Session = Depends(get_db)
):
    """
    Multistep Agent Router:
    Uses Mistral Function Calling to classify intent into:
    • search_video (timestamped search)
    • ask_question (grounded RAG with citations)
    • translate_dub (voiceover generation)
    • chat (general conversation)
    • orchestrated (multi-part question decomposition, sub-loop dispatch, and composite verification)
    """
    video = db.query(Video).filter(Video.id == video_id).first()
    if not video:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Video '{video_id}' not found")

    session_id = payload.session_id or "default-session"
    if mode == "baseline":
        result = route_user_intent_baseline(payload.message, video_id, db, session_id=session_id)
        result.update(mode="baseline", tool_call_count=0 if result.get("type") == "chat" else 1, model_used=get_llm_model(), provider_used=get_llm_provider())
    elif mode == "orchestrated":
        result = run_orchestrated_agent(payload.message, video_id, db, session_id=session_id)
    else:
        result = run_agent_loop(payload.message, video_id, db, session_id=session_id)
    return AgentChatResponse(**result)
