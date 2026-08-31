"""Unified LLM and Embeddings Client supporting Gemini, OpenAI, Mistral, Ollama, and OpenAI-compatible providers."""

from __future__ import annotations

import logging
from typing import Any, Optional

from app.core.config import settings

logger = logging.getLogger(__name__)

_client: Optional[UnifiedLLMClient] = None
_last_config: Optional[tuple[str, str, str]] = None


class ChatAdapter:
    """Provides compatibility between OpenAI, Gemini, and Mistral chat interfaces."""

    def __init__(self, openai_client: Any) -> None:
        self._openai = openai_client
        self.completions = openai_client.chat.completions

    def complete(self, *args: Any, **kwargs: Any) -> Any:
        """Mistral-style `.chat.complete(...)` mapped to standard OpenAI `.chat.completions.create(...)`."""
        return self._openai.chat.completions.create(*args, **kwargs)

    def create(self, *args: Any, **kwargs: Any) -> Any:
        """Standard OpenAI-style `.chat.completions.create(...)`."""
        return self._openai.chat.completions.create(*args, **kwargs)


class EmbeddingAdapter:
    """Provides compatibility across embedding interfaces."""

    def __init__(self, openai_client: Any) -> None:
        self._openai = openai_client

    def create(self, *args: Any, **kwargs: Any) -> Any:
        # Mistral uses inputs=..., OpenAI/Gemini use input=...
        if "inputs" in kwargs and "input" not in kwargs:
            kwargs["input"] = kwargs.pop("inputs")
        return self._openai.embeddings.create(*args, **kwargs)


class UnifiedLLMClient:
    """Unified client for Gemini, OpenAI, Mistral, Ollama, and custom endpoints."""

    def __init__(self, api_key: str, base_url: str, provider: str) -> None:
        from openai import OpenAI

        self.provider = provider
        self.base_url = base_url
        self._raw_client = OpenAI(api_key=api_key or "dummy-key", base_url=base_url)
        self.chat = ChatAdapter(self._raw_client)
        self.embeddings = EmbeddingAdapter(self._raw_client)

        # Voxtral TTS Audio support
        if settings.MISTRAL_API_KEY:
            try:
                try:
                    from mistralai import Mistral
                except ImportError:
                    from mistralai.client import Mistral
                self.audio = Mistral(api_key=settings.MISTRAL_API_KEY).audio
            except Exception:
                self.audio = getattr(self._raw_client, "audio", None)
        else:
            self.audio = getattr(self._raw_client, "audio", None)

    @property
    def raw_client(self) -> Any:
        return self._raw_client


def get_llm_client() -> Optional[UnifiedLLMClient]:
    """Return the shared LLM client initialized for the configured provider, or None if unconfigured."""
    global _client, _last_config

    provider = settings.get_effective_llm_provider()
    api_key = settings.get_effective_llm_api_key()
    base_url = settings.get_effective_llm_base_url()
    model = settings.get_effective_llm_model()

    current_config = (provider, api_key, base_url)
    if _client is not None and _last_config == current_config:
        return _client

    if not api_key and provider not in {"ollama", "custom"}:
        return None

    try:
        _client = UnifiedLLMClient(api_key=api_key, base_url=base_url, provider=provider)
        _last_config = current_config
        logger.info("Unified LLM client initialized (provider=%s, model=%s, base_url=%s)", provider, model, base_url)
    except Exception as exc:
        logger.warning("Could not initialize Unified LLM client: %s", exc)
        return None

    return _client


def get_llm_provider() -> str:
    """Return the active LLM provider name (e.g. gemini, openai, mistral)."""
    return settings.get_effective_llm_provider()


def get_llm_model() -> str:
    """Return the active LLM model name."""
    return settings.get_effective_llm_model()


_embed_client: Optional[UnifiedLLMClient] = None
_last_embed_config: Optional[tuple[str, str, str]] = None
_tts_client: Any = None
_last_tts_key: Optional[str] = None


def get_embedding_client() -> Optional[UnifiedLLMClient]:
    """Return the client configured for embeddings generation."""
    global _embed_client, _last_embed_config

    provider = settings.get_effective_embedding_provider()
    api_key = settings.get_effective_embedding_api_key()
    base_url = settings.get_effective_embedding_base_url()

    current_config = (provider, api_key, base_url)
    if _embed_client is not None and _last_embed_config == current_config:
        return _embed_client

    if not api_key and provider not in {"ollama", "custom"}:
        return None

    try:
        _embed_client = UnifiedLLMClient(api_key=api_key, base_url=base_url, provider=provider)
        _last_embed_config = current_config
        logger.info("Embedding client initialized (provider=%s, base_url=%s)", provider, base_url)
    except Exception as exc:
        logger.warning("Could not initialize Embedding client: %s", exc)
        return None

    return _embed_client


def get_embedding_model() -> str:
    """Return the active embedding model name."""
    return settings.get_effective_embedding_model()


def get_mistral_tts_client() -> Any:
    """Return a native Mistral client for Voxtral TTS speech generation."""
    global _tts_client, _last_tts_key

    if not settings.MISTRAL_API_KEY:
        return None

    if _tts_client is not None and _last_tts_key == settings.MISTRAL_API_KEY:
        return _tts_client

    try:
        try:
            from mistralai import Mistral
        except ImportError:
            from mistralai.client import Mistral
        _tts_client = Mistral(api_key=settings.MISTRAL_API_KEY)
        _last_tts_key = settings.MISTRAL_API_KEY
        return _tts_client
    except Exception as exc:
        logger.warning("Could not initialize Mistral TTS client: %s", exc)
        return None


# Convenience aliases for backward compatibility across service modules
get_mistral_client = get_llm_client
EMBED_MODEL = settings.MISTRAL_EMBED_MODEL
LLM_MODEL = settings.get_effective_llm_model()
TTS_MODEL = settings.MISTRAL_TTS_MODEL
