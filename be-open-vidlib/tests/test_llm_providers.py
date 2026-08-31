"""Tests for unified LLM provider resolution, client adapters, and multi-provider compatibility."""

from unittest.mock import MagicMock, patch
from app.core.config import Settings
from app.core.llm_client import UnifiedLLMClient, ChatAdapter, EmbeddingAdapter, get_llm_client


def test_provider_resolution_defaults():
    settings = Settings(_env_file=None, MISTRAL_API_KEY="test-mistral-key")
    assert settings.get_effective_llm_provider() == "mistral"
    assert settings.get_effective_llm_api_key() == "test-mistral-key"
    assert settings.get_effective_llm_base_url() == "https://api.mistral.ai/v1"
    assert settings.get_effective_llm_model() == "mistral-small-latest"
    assert settings.get_effective_embedding_provider() == "mistral"
    assert settings.get_effective_embedding_model() == "mistral-embed"


def test_provider_resolution_openai():
    settings = Settings(_env_file=None, OPENAI_API_KEY="test-openai-key", MISTRAL_API_KEY="", GEMINI_API_KEY="", GOOGLE_API_KEY="")
    assert settings.get_effective_llm_provider() == "openai"
    assert settings.get_effective_llm_api_key() == "test-openai-key"
    assert settings.get_effective_llm_base_url() == "https://api.openai.com/v1"
    assert settings.get_effective_llm_model() == "gpt-4o-mini"
    assert settings.get_effective_embedding_provider() == "openai"
    assert settings.get_effective_embedding_model() == "text-embedding-3-small"


def test_provider_resolution_gemini():
    settings = Settings(_env_file=None, GEMINI_API_KEY="test-gemini-key", MISTRAL_API_KEY="", OPENAI_API_KEY="", DEEPSEEK_API_KEY="")
    assert settings.get_effective_llm_provider() == "gemini"
    assert settings.get_effective_llm_api_key() == "test-gemini-key"
    assert settings.get_effective_llm_base_url() == "https://generativelanguage.googleapis.com/v1beta/openai/"
    assert settings.get_effective_llm_model() == "gemini-2.5-flash"
    assert settings.get_effective_embedding_provider() == "gemini"
    assert settings.get_effective_embedding_model() == "gemini-embedding-2"


def test_provider_resolution_deepseek():
    settings = Settings(_env_file=None, DEEPSEEK_API_KEY="test-deepseek-key", MISTRAL_API_KEY="", GEMINI_API_KEY="", GOOGLE_API_KEY="", OPENAI_API_KEY="")
    assert settings.get_effective_llm_provider() == "deepseek"
    assert settings.get_effective_llm_api_key() == "test-deepseek-key"
    assert settings.get_effective_llm_base_url() == "https://api.deepseek.com/v1"
    assert settings.get_effective_llm_model() == "deepseek-chat"


def test_provider_resolution_gemini_defaults():
    settings = Settings(_env_file=None, GEMINI_API_KEY="test-gemini-key", MISTRAL_API_KEY="")
    assert settings.get_effective_llm_provider() == "gemini"
    assert settings.get_effective_llm_api_key() == "test-gemini-key"
    assert settings.get_effective_llm_base_url() == "https://generativelanguage.googleapis.com/v1beta/openai/"
    assert settings.get_effective_llm_model() == "gemini-2.5-flash"
    assert settings.get_effective_embedding_provider() == "gemini"
    assert settings.get_effective_embedding_model() == "gemini-embedding-2"


def test_embedding_resolution_independent_override():
    # Explicitly choose Mistral embeddings while using OpenAI for the agent loop
    settings = Settings(
        _env_file=None,
        LLM_PROVIDER="openai",
        OPENAI_API_KEY="test-openai-key",
        EMBEDDING_PROVIDER="mistral",
        MISTRAL_API_KEY="test-mistral-key"
    )
    assert settings.get_effective_llm_provider() == "openai"
    assert settings.get_effective_embedding_provider() == "mistral"
    assert settings.get_effective_embedding_model() == "mistral-embed"


def test_explicit_provider_override():
    settings = Settings(
        _env_file=None,
        LLM_PROVIDER="custom",
        LLM_API_KEY="custom-key",
        LLM_BASE_URL="http://localhost:11434/v1",
        LLM_MODEL="llama3.1"
    )
    assert settings.get_effective_llm_provider() == "custom"
    assert settings.get_effective_llm_api_key() == "custom-key"
    assert settings.get_effective_llm_base_url() == "http://localhost:11434/v1"
    assert settings.get_effective_llm_model() == "llama3.1"


def test_chat_adapter_complete_maps_to_completions_create():
    mock_openai = MagicMock()
    mock_openai.chat.completions.create.return_value = "response-mock"
    adapter = ChatAdapter(mock_openai)
    
    res = adapter.complete(model="gpt-4o-mini", messages=[{"role": "user", "content": "hi"}])
    assert res == "response-mock"
    mock_openai.chat.completions.create.assert_called_once_with(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": "hi"}]
    )


def test_embedding_adapter_translates_inputs_arg():
    mock_openai = MagicMock()
    mock_openai.embeddings.create.return_value = "embed-mock"
    adapter = EmbeddingAdapter(mock_openai)
    
    res = adapter.create(model="text-embedding-3-small", inputs=["a", "b"])
    assert res == "embed-mock"
    mock_openai.embeddings.create.assert_called_once_with(
        model="text-embedding-3-small",
        input=["a", "b"]
    )


def test_mistral_tts_client_available_when_mistral_key_configured():
    from app.core.llm_client import get_mistral_tts_client
    settings = Settings(
        LLM_PROVIDER="openai",
        OPENAI_API_KEY="test-openai-key",
        MISTRAL_API_KEY="test-mistral-key"
    )
    with patch("app.core.llm_client.settings", settings):
        with patch("mistralai.client.Mistral") as mock_mistral:
            client = get_mistral_tts_client()
            assert client is not None
            mock_mistral.assert_called_once_with(api_key="test-mistral-key")
