"""
Backward-compatible wrapper for the unified LLM client.
Supports Gemini, OpenAI, Mistral, Ollama, and OpenAI-compatible providers.
"""

from app.core.llm_client import (
    get_llm_client,
    get_mistral_client,
    get_embedding_client,
    get_embedding_model,
    get_mistral_tts_client,
    get_llm_provider,
    get_llm_model,
    EMBED_MODEL,
    LLM_MODEL,
    TTS_MODEL,
    UnifiedLLMClient,
    ChatAdapter,
    EmbeddingAdapter,
)

__all__ = [
    "get_llm_client",
    "get_mistral_client",
    "get_embedding_client",
    "get_embedding_model",
    "get_mistral_tts_client",
    "get_llm_provider",
    "get_llm_model",
    "EMBED_MODEL",
    "LLM_MODEL",
    "TTS_MODEL",
    "UnifiedLLMClient",
    "ChatAdapter",
    "EmbeddingAdapter",
]
