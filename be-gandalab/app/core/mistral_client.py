"""
Lazy singleton for the Mistral AI client.

The app works without a key — search and Q&A fall back to deterministic
heuristics. Set MISTRAL_API_KEY in your .env to unlock the full pipeline.
"""
import logging
from typing import Optional, Any

from app.core.config import settings

logger = logging.getLogger(__name__)

_client: Optional[Any] = None


def get_mistral_client() -> Optional[Any]:
    """Return the shared Mistral client, or None if no key is configured."""
    global _client
    if _client is not None:
        return _client

    if not settings.MISTRAL_API_KEY:
        return None

    try:
        from mistralai import Mistral
        _client = Mistral(api_key=settings.MISTRAL_API_KEY)
        logger.info("Mistral client initialised (model=%s)", settings.MISTRAL_LLM_MODEL)
    except Exception as exc:
        logger.warning("Could not initialise Mistral client: %s", exc)

    return _client


# Convenience aliases used across service modules
EMBED_MODEL = settings.MISTRAL_EMBED_MODEL
LLM_MODEL = settings.MISTRAL_LLM_MODEL
TTS_MODEL = settings.MISTRAL_TTS_MODEL
