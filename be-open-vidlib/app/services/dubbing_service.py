import os
import json
import logging
from pathlib import Path
from sqlalchemy.orm import Session
from app.core.voice_presets import get_voice_id
from app.services.translation_service import translate_segment
from app.services.tts_service import generate_speech
from app.models.video_segment import VideoSegment
from app.models.audio_dub import AudioDub

logger = logging.getLogger(__name__)

SUPPORTED_DUB_LANGUAGES = {"en", "fr"}


def _caption_manifest_path(video_id: str, language: str) -> Path:
    return Path(f"static/dubs/{video_id}/{language}/captions.json")


def load_translated_captions(video_id: str, language: str) -> dict[int, str]:
    """Load the persistent translated caption text for a cached audio track."""
    path = _caption_manifest_path(video_id, language.lower())
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
        return {int(item["segment_id"]): str(item["text"]) for item in payload if item.get("text")}
    except (FileNotFoundError, json.JSONDecodeError, TypeError, ValueError, KeyError):
        return {}

def create_dubbed_track(video_id: str, target_lang: str, voice_gender: str, db: Session) -> dict:
    """
    Translate segments for video -> generate Voxtral audio dubs -> store metadata.
    """
    target_lang = target_lang.lower()
    if target_lang not in SUPPORTED_DUB_LANGUAGES:
        raise ValueError("Dubbing is currently available only in English and French.")

    voice_id = get_voice_id(target_lang, voice_gender)
    segments = db.query(VideoSegment).filter(
        VideoSegment.video_id == video_id
    ).order_by(VideoSegment.start_time.asc()).all()

    dubbed_segments = []
    translated_captions = load_translated_captions(video_id, target_lang)

    for seg in segments:
        existing_dub = db.query(AudioDub).filter(
            AudioDub.video_id == video_id,
            AudioDub.segment_id == seg.id,
            AudioDub.language == target_lang
        ).first()
        if existing_dub and Path(existing_dub.audio_path.lstrip(chr(47))).exists() and Path(existing_dub.audio_path.lstrip(chr(47))).stat().st_size > 1024:
            if seg.id not in translated_captions:
                translated_captions[seg.id] = seg.text if target_lang == "en" else translate_segment(seg.text, target_lang)
                seg.translated_text = translated_captions[seg.id]
            dubbed_segments.append(existing_dub)
            continue

        # 1. Translate the exact caption window used by the audio segment.
        translated = translate_segment(seg.text, target_lang)
        translated_captions[seg.id] = translated
        seg.translated_text = translated

        # 2. Generate speech
        rel_path = f"static/dubs/{video_id}/{target_lang}/seg_{seg.id}.mp3"
        generated_path = generate_speech(translated, voice_id, rel_path)
        if not generated_path:
            raise RuntimeError("Audio generation failed; no dubbed audio was cached")

        # 3. Store / update AudioDub metadata
        existing_dub = db.query(AudioDub).filter(
            AudioDub.video_id == video_id,
            AudioDub.segment_id == seg.id,
            AudioDub.language == target_lang
        ).first()

        if not existing_dub:
            dub = AudioDub(
                video_id=video_id,
                segment_id=seg.id,
                language=target_lang,
                audio_path=f"/static/dubs/{video_id}/{target_lang}/seg_{seg.id}.mp3",
                start_time=seg.start_time,
                end_time=seg.end_time,
                voice_id=voice_id
            )
            db.add(dub)
            dubbed_segments.append(dub)
        else:
            existing_dub.audio_path = f"/static/dubs/{video_id}/{target_lang}/seg_{seg.id}.mp3"
            existing_dub.voice_id = voice_id
            dubbed_segments.append(existing_dub)

    db.commit()

    manifest_path = _caption_manifest_path(video_id, target_lang)
    manifest_path.parent.mkdir(parents=True, exist_ok=True)
    manifest_path.write_text(
        json.dumps(
            [
                {
                    "segment_id": d.segment_id,
                    "start": d.start_time,
                    "end": d.end_time,
                    "text": translated_captions.get(d.segment_id, ""),
                }
                for d in dubbed_segments
            ],
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )

    return {
        "video_id": video_id,
        "language": target_lang,
        "voice": voice_id,
        "status": "completed",
        "segments": [
            {
                "segment_id": d.segment_id,
                "audio_url": d.audio_path,
                "start": d.start_time,
                "end": d.end_time,
                "translated_text": translated_captions.get(d.segment_id) or getattr(d.segment, "translated_text", None) if d.segment else translated_captions.get(d.segment_id)
            }
            for d in dubbed_segments
        ]
    }
