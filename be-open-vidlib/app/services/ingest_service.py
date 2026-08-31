import hashlib
import logging
import math
import re
from typing import Any, Dict, List

from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.mistral_client import EMBED_MODEL, get_embedding_client, get_embedding_model, get_mistral_client
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


def _build_chunks(captions: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    if not captions:
        return []

    chunks: List[Dict[str, Any]] = []
    i = 0
    while i < len(captions):
        start = captions[i]["start"]
        buf: List[str] = []
        end = captions[i]["end"]
        j = i
        while j < len(captions):
            t = captions[j]["text"].strip()
            tentative = " ".join(buf + [t]) if buf else t
            if buf and len(tentative) > MAX_CHARS:
                break
            buf.append(t)
            end = captions[j]["end"]
            j += 1
            if len(" ".join(buf)) >= TARGET_CHARS:
                break

        chunks.append({
            "text": re.sub(r"\s+", " ", " ".join(buf)).strip(),
            "start": float(start),
            "end": float(end),
            "start_time": float(start),
            "end_time": float(end),
        })

        if j >= len(captions):
            break
        i = max(i + 1, j - OVERLAP_CAPTIONS)

    return chunks


def chunk_and_embed(video_id: str, captions: List[Dict[str, Any]], db: Session, language: str = "en") -> int:
    """Create overlapping transcript windows and embed them in one API batch."""
    chunks = _build_chunks(captions)
    if not chunks:
        return 0

    texts = [chunk["text"] for chunk in chunks]
    client = get_embedding_client() or get_mistral_client()
    embed_model = get_embedding_model()
    if client and (settings.MISTRAL_API_KEY or settings.get_effective_embedding_api_key()):
        try:
            response = client.embeddings.create(model=embed_model, inputs=texts)
            embeddings = [item.embedding for item in response.data]
        except Exception as exc:
            logger.warning("Embedding generation failed, using deterministic fallback: %s", exc)
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
