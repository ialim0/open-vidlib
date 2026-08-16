import hashlib
import logging
import math
import re
from collections import Counter
from typing import Any, Dict, Iterable, List

from sqlalchemy import text
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.mistral_client import EMBED_MODEL, get_mistral_client
from app.models.video_segment import VideoSegment

logger = logging.getLogger(__name__)

_STOPWORDS = {"a", "an", "and", "are", "as", "at", "be", "by", "do", "for", "from", "how", "in", "is", "it", "of", "on", "or", "that", "the", "this", "to", "was", "what", "when", "where", "which", "who", "why", "with"}


def _get_mock_embedding(text_value: str, dim: int = 1024) -> List[float]:
    seed = int(hashlib.md5(text_value.encode("utf-8")).hexdigest(), 16)
    vec = [math.sin(seed + i) for i in range(dim)]
    norm = math.sqrt(sum(x * x for x in vec)) or 1.0
    return [x / norm for x in vec]


def _tokens(value: str) -> List[str]:
    return [token for token in re.findall(r"[\w']+", value.lower()) if token not in _STOPWORDS and len(token) > 1]


def _cosine_similarity(a: Iterable[float], b: Iterable[float]) -> float:
    left, right = list(a), list(b)
    dot = sum(x * y for x, y in zip(left, right))
    norm_a = math.sqrt(sum(x * x for x in left)) or 1.0
    norm_b = math.sqrt(sum(y * y for y in right)) or 1.0
    return dot / (norm_a * norm_b)


def _lexical_scores(query: str, segments: List[VideoSegment]) -> Dict[int, float]:
    query_terms = Counter(_tokens(query))
    if not query_terms:
        return {segment.id: 0.0 for segment in segments}

    documents = {segment.id: _tokens(segment.text) for segment in segments}
    document_frequency = Counter(term for terms in documents.values() for term in set(terms))
    total = max(len(documents), 1)
    scores: Dict[int, float] = {}
    for segment_id, terms in documents.items():
        term_frequency = Counter(terms)
        length_norm = 0.5 + 0.5 * (len(terms) / max(1, 420))
        score = 0.0
        for term, query_frequency in query_terms.items():
            if term not in term_frequency:
                continue
            idf = math.log((total + 1) / (document_frequency[term] + 1)) + 1.0
            score += idf * (term_frequency[term] / length_norm) * min(query_frequency, 2)
        scores[segment_id] = score
    return scores


def _result(segment: VideoSegment, similarity: float) -> Dict[str, Any]:
    return {
        "text": segment.text,
        "start_time": float(segment.start_time),
        "end_time": float(segment.end_time),
        "similarity": float(max(0.0, min(1.0, similarity))),
    }


def search_video(video_id: str, query: str, db: Session, top_k: int = 5) -> List[Dict[str, Any]]:
    query = re.sub(r"\s+", " ", query or "").strip()
    if not query:
        return []
    top_k = max(1, min(int(top_k), 20))
    segments = db.query(VideoSegment).filter(VideoSegment.video_id == video_id).all()
    if not segments:
        return []

    client = get_mistral_client()
    if client and settings.MISTRAL_API_KEY:
        try:
            response = client.embeddings.create(model=EMBED_MODEL, inputs=[query])
            query_vec = response.data[0].embedding
        except Exception as exc:
            logger.warning("Failed to embed query, using fallback: %s", exc)
            query_vec = _get_mock_embedding(query)
    else:
        query_vec = _get_mock_embedding(query)

    vector_scores: Dict[int, float] = {}
    dialect = db.bind.dialect.name if db.bind else ""
    if dialect == "postgresql":
        try:
            rows = db.execute(text("""
                SELECT id, 1 - (embedding <=> CAST(:query_vec AS vector)) AS score
                FROM video_segments
                WHERE video_id = :video_id AND embedding IS NOT NULL
                ORDER BY embedding <=> CAST(:query_vec AS vector)
                LIMIT :candidate_limit
            """), {
                "query_vec": str(query_vec),
                "video_id": video_id,
                "candidate_limit": min(len(segments), max(30, top_k * 6)),
            }).mappings().all()
            vector_scores = {int(row["id"]): float(row["score"]) for row in rows}
        except Exception as exc:
            logger.warning("Vector search failed; using in-memory similarity: %s", exc)

    if not vector_scores:
        vector_scores = {
            segment.id: _cosine_similarity(query_vec, segment.embedding)
            for segment in segments
            if isinstance(segment.embedding, list) and len(segment.embedding) == len(query_vec)
        }

    lexical_scores = _lexical_scores(query, segments)
    vector_ranked = [item_id for item_id, _ in sorted(vector_scores.items(), key=lambda item: item[1], reverse=True)]
    lexical_ranked = [item_id for item_id, score in sorted(lexical_scores.items(), key=lambda item: item[1], reverse=True) if score > 0]
    vector_rank = {item_id: rank for rank, item_id in enumerate(vector_ranked)}
    lexical_rank = {item_id: rank for rank, item_id in enumerate(lexical_ranked)}

    # Reciprocal Rank Fusion makes lexical exact matches and semantic matches comparable.
    fused: Dict[int, float] = {}
    for segment in segments:
        item_id = segment.id
        fused[item_id] = (1 / (60 + vector_rank[item_id]) if item_id in vector_rank else 0) + (1 / (60 + lexical_rank[item_id]) if item_id in lexical_rank else 0)

    by_id = {segment.id: segment for segment in segments}
    ranked = sorted(fused, key=fused.get, reverse=True)
    selected: List[VideoSegment] = []
    selected_tokens: List[set[str]] = []
    for item_id in ranked:
        segment = by_id[item_id]
        tokens = set(_tokens(segment.text))
        redundancy = max((len(tokens & other) / max(1, len(tokens | other)) for other in selected_tokens), default=0.0)
        if redundancy > 0.82 and len(selected) < top_k:
            continue
        selected.append(segment)
        selected_tokens.append(tokens)
        if len(selected) == top_k:
            break

    maximum = max((fused[segment.id] for segment in selected), default=1.0)
    return [_result(segment, fused[segment.id] / maximum) for segment in selected]
