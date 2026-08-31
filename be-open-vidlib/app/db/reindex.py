"""Rebuild transcript chunks and embeddings without recreating the database."""
import json
import logging
from pathlib import Path

from app.core.database import SessionLocal
from app.models.video import Video
from app.services.ingest_service import chunk_and_embed

logging.basicConfig(level=logging.INFO, format="%(levelname)s %(name)s: %(message)s")
logger = logging.getLogger(__name__)

VIDEO_PREFIXES = {
    "video-0": "s",
    "video-2": "e",
    "video-3": "m",
}


def _captions(words: list[dict]) -> list[dict]:
    captions = []
    current_words = []
    current_start = None
    for word in words:
        if current_start is None:
            current_start = word.get("start", 0.0)
        current_words.append(word.get("word", ""))
        if len(current_words) >= 10 or word.get("word", "").endswith((".", "!", "?")):
            captions.append({
                "text": " ".join(current_words),
                "start": current_start,
                "end": word.get("end", current_start),
            })
            current_words = []
            current_start = None
    if current_words:
        captions.append({
            "text": " ".join(current_words),
            "start": current_start or 0.0,
            "end": words[-1].get("end", 0.0),
        })
    return captions


def reindex() -> None:
    seed_dir = Path(__file__).parent / "seed_data"
    db = SessionLocal()
    try:
        for video_id, prefix in VIDEO_PREFIXES.items():
            if not db.query(Video).filter(Video.id == video_id).first():
                logger.warning("Skipping missing video %s", video_id)
                continue
            for transcript_file in sorted(seed_dir.glob(f"{prefix}-video-*.txt")):
                language = transcript_file.stem.split("-")[-1]
                data = json.loads(transcript_file.read_text(encoding="utf-8"))
                words = data.get("words", [])
                count = chunk_and_embed(video_id, _captions(words), db, language=language)
                logger.info("%s/%s: rebuilt %s retrieval chunks", video_id, language, count)
    finally:
        db.close()


if __name__ == "__main__":
    reindex()
