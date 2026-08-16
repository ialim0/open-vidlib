import logging
import math
import hashlib
from typing import List, Dict, Any
from sqlalchemy import text
from sqlalchemy.orm import Session
from app.core.config import settings
from app.core.mistral_client import get_mistral_client, EMBED_MODEL
from app.models.video_segment import VideoSegment

logger = logging.getLogger(__name__)

def _get_mock_embedding(text: str, dim: int = 1024) -> List[float]:
    seed = int(hashlib.md5(text.encode("utf-8")).hexdigest(), 16)
    vec = [math.sin(seed + i) for i in range(dim)]
    norm = math.sqrt(sum(x * x for x in vec)) or 1.0
    return [x / norm for x in vec]

def _cosine_similarity(a: List[float], b: List[float]) -> float:
    dot = sum(x * y for x, y in zip(a, b))
    norm_a = math.sqrt(sum(x * x for x in a)) or 1.0
    norm_b = math.sqrt(sum(y * y for y in b)) or 1.0
    return dot / (norm_a * norm_b)

def search_video(video_id: str, query: str, db: Session, top_k: int = 5) -> List[Dict[str, Any]]:
    # 1. Embed query
    client = get_mistral_client()
    query_vec = None

    if client and settings.MISTRAL_API_KEY:
        try:
            emb_response = client.embeddings.create(
                model=EMBED_MODEL,
                inputs=[query]
            )
            query_vec = emb_response.data[0].embedding
        except Exception as e:
            logger.warning(f"Failed to embed query via Mistral, using fallback: {e}")
            query_vec = _get_mock_embedding(query)
    else:
        query_vec = _get_mock_embedding(query)

    # 2. Vector search (pgvector if on PostgreSQL, Python cosine math if SQLite/other)
    bind_dialect = db.bind.dialect.name if db.bind else ""
    if bind_dialect == "postgresql":
        try:
            sql = text("""
                SELECT text, start_time, end_time,
                       1 - (embedding <=> :query_vec) AS similarity
                FROM video_segments
                WHERE video_id = :video_id
                ORDER BY embedding <=> :query_vec
                LIMIT :top_k
            """)
            results = db.execute(sql, {
                "query_vec": str(query_vec),
                "video_id": video_id,
                "top_k": top_k
            }).mappings().all()

            return [
                {
                    "text": r["text"],
                    "start_time": float(r["start_time"]),
                    "end_time": float(r["end_time"]),
                    "similarity": float(r["similarity"])
                }
                for r in results
            ]
        except Exception as e:
            logger.warning(f"PostgreSQL pgvector query error: {e}. Falling back to ORM retrieval.")

    # In-memory cosine calculation fallback (e.g. SQLite testing / local mock)
    segments = db.query(VideoSegment).filter(VideoSegment.video_id == video_id).all()
    if not segments:
        return []

    scored_segments = []
    for s in segments:
        emb = s.embedding
        if isinstance(emb, list) and len(emb) == len(query_vec):
            sim = _cosine_similarity(query_vec, emb)
        else:
            # Simple keyword matching boost if embedding is empty
            query_words = set(query.lower().split())
            seg_words = set(s.text.lower().split())
            overlap = len(query_words.intersection(seg_words))
            sim = min(0.95, overlap / (len(query_words) or 1))

        scored_segments.append({
            "text": s.text,
            "start_time": s.start_time,
            "end_time": s.end_time,
            "similarity": float(sim)
        })

    scored_segments.sort(key=lambda x: x["similarity"], reverse=True)
    return scored_segments[:top_k]
