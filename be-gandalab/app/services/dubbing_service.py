import os
import logging
from sqlalchemy.orm import Session
from app.core.voice_presets import get_voice_id
from app.services.translation_service import translate_segment
from app.services.tts_service import generate_speech
from app.models.video_segment import VideoSegment
from app.models.audio_dub import AudioDub

logger = logging.getLogger(__name__)

def create_dubbed_track(video_id: str, target_lang: str, voice_gender: str, db: Session) -> dict:
    """
    Translate segments for video -> generate Voxtral audio dubs -> store metadata.
    """
    voice_id = get_voice_id(target_lang, voice_gender)
    segments = db.query(VideoSegment).filter(
        VideoSegment.video_id == video_id
    ).order_by(VideoSegment.start_time.asc()).all()

    dubbed_segments = []

    for seg in segments:
        # 1. Translate
        translated = translate_segment(seg.text, target_lang)
        seg.translated_text = translated

        # 2. Generate speech
        rel_path = f"static/dubs/{video_id}/{target_lang}/seg_{seg.id}.mp3"
        generate_speech(translated, voice_id, rel_path)

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
                "translated_text": getattr(d.segment, "translated_text", None) if d.segment else None
            }
            for d in dubbed_segments
        ]
    }
