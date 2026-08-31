import json
import logging
from pathlib import Path
from sqlalchemy.orm import Session
from app.core.database import SessionLocal, Base, engine
from app.models.video import Video
from app.models.transcript import Transcript
from app.models.flashcard import Flashcard
from app.services.ingest_service import chunk_and_embed

logger = logging.getLogger(__name__)

SEED_VIDEOS = [
    {
        "id": "video-0",
        "slug": "science-gravity-explained",
        "title": "La Gravité Expliquée aux Enfants",
        "category": "Science",
        "url": "https://youtu.be/suQDwZcnJdg?si=Sci2Buj-E5ZDn94G",
        "cover_image": "/science/img-1.png",
        "description": "Une leçon interactive et passionnante pour comprendre la gravité terrestre, la chute des corps et les lois de Newton.",
        "duration_seconds": 240,
        "prefix": "s"
    },
    {
        "id": "video-2",
        "slug": "engineering-pyramid-of-cheops",
        "title": "Les chiffres affolants de la pyramide de Khéops",
        "category": "Engineering",
        "url": "https://youtu.be/ITYFvAP98qs?si=SumofslEc4X48MSx",
        "cover_image": "/engineering/img-1.png",
        "description": "Explorez les prouesses architecturales, les dimensions colossales et les secrets d'ingénierie de la grande pyramide.",
        "duration_seconds": 420,
        "prefix": "e"
    },
    {
        "id": "video-3",
        "slug": "mathematics-pythagorean-theorem",
        "title": "À quoi sert le théorème de Pythagore ?",
        "category": "Mathematics",
        "url": "https://youtu.be/eYQPZgMTzkY?si=5UWldu8ZcR4Kg5R9",
        "cover_image": "/mathematics/img-1.png",
        "description": "Comprenez l'utilité pratique du théorème de Pythagore dans la construction, la navigation et la vie quotidienne.",
        "duration_seconds": 280,
        "prefix": "m"
    }
]

def seed_database(db: Session = None):
    close_session = False
    if db is None:
        db = SessionLocal()
        close_session = True

    try:
        # Check if database is already seeded
        existing_count = db.query(Video).count()
        if existing_count > 0:
            logger.info(f"Database already contains {existing_count} videos. Skipping initial seeding.")
            return

        logger.info("Seeding database with educational videos, transcripts, pgvector chunks, and flashcards...")
        seed_dir = Path(__file__).parent / "seed_data"
        flashcards_dir = seed_dir / "flashcards"

        for v_data in SEED_VIDEOS:
            prefix = v_data.pop("prefix")
            video = Video(**v_data)
            db.add(video)
            db.flush()

            # Seed Transcripts & Ingest pgvector Chunks
            transcript_files = list(seed_dir.glob(f"{prefix}-video-*.txt"))
            for t_file in transcript_files:
                lang_match = t_file.stem.split("-")[-1] # e.g. 'en' or 'fr'
                try:
                    with open(t_file, "r", encoding="utf-8") as f:
                        data = json.load(f)
                    
                    if "words" in data and isinstance(data["words"], list):
                        words = data["words"]
                        full_text = " ".join([w.get("word", "") for w in words])
                        transcript = Transcript(
                            video_id=video.id,
                            language=lang_match,
                            full_text=full_text,
                            words=words,
                            segments=data.get("segments", None)
                        )
                        db.add(transcript)

                        # Create captions format for chunking & embedding
                        # Group words into small sentence captions
                        captions = []
                        curr_words = []
                        curr_start = None
                        for w in words:
                            if curr_start is None:
                                curr_start = w.get("start", 0.0)
                            curr_words.append(w.get("word", ""))
                            if len(curr_words) >= 10 or w.get("word", "").endswith((".", "!", "?")):
                                captions.append({
                                    "text": " ".join(curr_words),
                                    "start": curr_start,
                                    "end": w.get("end", curr_start)
                                })
                                curr_words = []
                                curr_start = None
                        if curr_words:
                            captions.append({
                                "text": " ".join(curr_words),
                                "start": curr_start if curr_start is not None else 0.0,
                                "end": words[-1].get("end", 0.0)
                            })

                        # Chunk & embed via ingest_service
                        chunk_and_embed(video.id, captions, db, language=lang_match)

                except Exception as e:
                    logger.warning(f"Could not parse transcript file {t_file}: {e}")

            # Seed Flashcards
            if flashcards_dir.exists():
                flashcard_files = list(flashcards_dir.glob(f"{prefix}-video-*.json"))
                for fc_file in flashcard_files:
                    lang_match = fc_file.stem.split("-")[-1]
                    try:
                        with open(fc_file, "r", encoding="utf-8") as f:
                            fc_data = json.load(f)
                        
                        cards = fc_data.get("flashcards", [])
                        for card in cards:
                            fc = Flashcard(
                                video_id=video.id,
                                language=lang_match,
                                question=card.get("question", ""),
                                options=card.get("options", []),
                                correct_option=card.get("correctOption", 0),
                                source=card.get("source", "")
                            )
                            db.add(fc)
                    except Exception as e:
                        logger.warning(f"Could not parse flashcard file {fc_file}: {e}")

        db.commit()
        logger.info("Database successfully seeded with Mistral embeddings & video library data!")
    except Exception as e:
        db.rollback()
        logger.error(f"Error seeding database: {e}")
        raise
    finally:
        if close_session:
            db.close()

if __name__ == "__main__":
    Base.metadata.create_all(bind=engine)
    seed_database()
