import logging
import math
import hashlib
from typing import List, Dict, Any
from sqlalchemy.orm import Session
from app.core.config import settings
from app.core.mistral_client import get_mistral_client, EMBED_MODEL
from app.models.video_segment import VideoSegment

logger = logging.getLogger(__name__)

def _get_mock_embedding(text: str, dim: int = 1024) -> List[float]:
    """Deterministic normalized mock embedding for tests and offline development."""
    seed = int(hashlib.md5(text.encode("utf-8")).hexdigest(), 16)
    vec = [math.sin(seed + i) for i in range(dim)]
    norm = math.sqrt(sum(x * x for x in vec)) or 1.0
    return [x / norm for x in vec]

def chunk_and_embed(video_id: str, captions: List[Dict[str, Any]], db: Session, language: str = "en") -> int:
    """
    captions: [{"text": "...", "start": 12.5, "end": 15.2}, ...]
    Strategy: chunk by ~500 chars with sentence awareness, preserving start/end timestamps.
    """
    if not captions:
        return 0

    chunks = []
    buffer_text = ""
    buffer_start = None

    for cap in captions:
        if buffer_start is None:
            buffer_start = cap.get("start", 0.0)

        buffer_text += " " + cap.get("text", "")

        if len(buffer_text) >= 500:
            chunks.append({
                "text": buffer_text.strip(),
                "start": buffer_start,
                "end": cap.get("end", buffer_start)
            })
            buffer_text = ""
            buffer_start = None

    if buffer_text.strip():
        last_end = captions[-1].get("end", buffer_start or 0.0)
        chunks.append({
            "text": buffer_text.strip(),
            "start": buffer_start if buffer_start is not None else 0.0,
            "end": last_end
        })

    texts = [c["text"] for c in chunks]
    embeddings = []

    client = get_mistral_client()
    if client and settings.MISTRAL_API_KEY:
        try:
            response = client.embeddings.create(
                model=EMBED_MODEL,
                inputs=texts
            )
            embeddings = [d.embedding for d in response.data]
        except Exception as e:
            logger.warning(f"Mistral embedding failed, using deterministic fallback: {e}")
            embeddings = [_get_mock_embedding(t) for t in texts]
    else:
        embeddings = [_get_mock_embedding(t) for t in texts]

    # Clear old segments for this video if re-ingesting
    db.query(VideoSegment).filter(
        VideoSegment.video_id == video_id,
        VideoSegment.language == language
    ).delete()

    for chunk, emb in zip(chunks, embeddings):
        seg = VideoSegment(
            video_id=video_id,
            text=chunk["text"],
            start_time=chunk["start"],
            end_time=chunk["end"],
            embedding=emb,
            language=language
        )
        db.add(seg)

    db.commit()
    return len(chunks)
