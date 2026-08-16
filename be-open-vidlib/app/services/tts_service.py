import base64
import os
import logging
from pathlib import Path
from typing import Optional
from app.core.config import settings
from app.core.mistral_client import get_mistral_client, TTS_MODEL

logger = logging.getLogger(__name__)

def generate_speech(text: str, voice_id: str, output_path: str) -> Optional[str]:
    """Generate audio via Voxtral TTS and save to disk."""
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    client = get_mistral_client()
    if not client or not settings.MISTRAL_API_KEY:
        logger.warning("TTS unavailable: set MISTRAL_API_KEY before generating dubbed audio")
        return None

    try:
        response = client.audio.speech.complete(
            model=TTS_MODEL,
            input=text,
            voice_id=voice_id,
            response_format="mp3"
        )
        if not hasattr(response, "audio_data"):
            logger.warning("TTS returned no audio data")
            return None
        audio_bytes = base64.b64decode(response.audio_data)
        if not audio_bytes:
            return None
        Path(output_path).write_bytes(audio_bytes)
        return output_path
    except Exception as e:
        logger.warning("Voxtral speech generation failed: %s", e)
        return None
