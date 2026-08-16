import hashlib
import logging
import math
import re
from typing import Any, Dict, List

from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.mistral_client import EMBED_MODEL, get_mistral_client
from app.models.video_segment import VideoSegment

logger = logging.getLogger(__name__)

TARGET_CHARS = 420
MAX_CHARS = 650
OVERLAP_CAPTIONS = 2


def _get_mock_embedding(text: str, dim: int = 1024) -> List[float]:
    """Deterministic normalized mock embedding for tests and offline development."""
    seed = int(hashlib.md5(text.encode("utf-8")).hexdigest(), 16)
    vec = [math.sin(seed + i) for i in range(dim)]
    norm = math.sqrt(sum(x * x for x in vec)) or 1.0
    return [x / norm for x in vec]


def _clean_caption(caption: Dict[str, Any]) -> Dict[str, Any] | None:
    text = re.sub(r"\s+", " ", str(caption.get("text", ""))).strip()
    if not text:
        return None
    start = float(caption.get("start", 0.0))
    end = max(start, float(caption.get("end", start)))
    return {"text": text, "start": start, "end": end}


def _build_chunks(captions: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Build timestamped, sentence-aware windows with small overlap for context continuity."""
    cleaned = [item for caption in captions if (item := _clean_caption(caption))]
    chunks: List[Dict[str, Any]] = []
    window: List[Dict[str, Any]] = []
    chars = 0

    for caption in cleaned:
        window.append(caption)
        chars += len(caption["text"]) + 1
        boundary = bool(re.search(r"[.!?]$", caption["text"]))
        if chars < TARGET_CHARS or (not boundary and chars < MAX_CHARS):
            continue

        chunks.append({
            "text": " ".join(item["text"] for item in window).strip(),
            "start": window[0]["start"],
            "end": window[-1]["end"],
        })
        window = window[-OVERLAP_CAPTIONS:]
        chars = sum(len(item["text"]) + 1 for item in window)

    if window:
        final = {
            "text": " ".join(item["text"] for item in window).strip(),
            "start": window[0]["start"],
            "end": window[-1]["end"],
        }
        if not chunks or final["text"] != chunks[-1]["text"]:
            chunks.append(final)
    return chunks


def chunk_and_embed(video_id: str, captions: List[Dict[str, Any]], db: Session, language: str = "en") -> int:
    """Create overlapping transcript windows and embed them in one API batch."""
    chunks = _build_chunks(captions)
    if not chunks:
        return 0

    texts = [chunk["text"] for chunk in chunks]
    client = get_mistral_client()
    if client and settings.MISTRAL_API_KEY:
        try:
            response = client.embeddings.create(model=EMBED_MODEL, inputs=texts)
            embeddings = [item.embedding for item in response.data]
        except Exception as exc:
            logger.warning("Mistral embedding failed, using deterministic fallback: %s", exc)
            embeddings = [_get_mock_embedding(text) for text in texts]
    else:
        embeddings = [_get_mock_embedding(text) for text in texts]

    db.query(VideoSegment).filter(
        VideoSegment.video_id == video_id,
        VideoSegment.language == language,
    ).delete()

    for chunk, embedding in zip(chunks, embeddings):
        db.add(VideoSegment(
            video_id=video_id,
            text=chunk["text"],
            start_time=chunk["start"],
            end_time=chunk["end"],
            embedding=embedding,
            language=language,
        ))

    db.commit()
    return len(chunks)
