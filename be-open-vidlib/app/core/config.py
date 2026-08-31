from typing import List, Optional, Union
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import field_validator


class Settings(BaseSettings):
    PROJECT_NAME: str = "Open VidLib API"
    VERSION: str = "1.0.0"
    API_V1_PREFIX: str = "/api/v1"

    # PostgreSQL + pgvector
    DATABASE_URL: str = "postgresql://postgres:postgres@localhost:5432/openvidlib"

    # LLM Providers (Gemini, OpenAI, Mistral, Ollama, OpenRouter, Groq, custom OpenAI-compatible)
    LLM_PROVIDER: Optional[str] = None
    LLM_API_KEY: str = ""
    LLM_BASE_URL: Optional[str] = None
    LLM_MODEL: Optional[str] = None

    # Google Gemini Provider Settings (OpenAI-compatible endpoint)
    GEMINI_API_KEY: str = ""
    GOOGLE_API_KEY: str = ""
    GEMINI_BASE_URL: Optional[str] = None
    GEMINI_MODEL: str = "gemini-2.5-flash"

    # OpenAI Provider Settings
    OPENAI_API_KEY: str = ""
    OPENAI_BASE_URL: Optional[str] = None
    OPENAI_MODEL: str = "gpt-4o-mini"

    # DeepSeek Provider Settings (Optional Alternative)
    DEEPSEEK_API_KEY: str = ""
    DEEPSEEK_BASE_URL: Optional[str] = None
    DEEPSEEK_MODEL: str = "deepseek-chat"

    # Embedding Settings (flexible independently from LLM provider)
    EMBEDDING_PROVIDER: Optional[str] = None
    EMBEDDING_API_KEY: Optional[str] = None
    EMBEDDING_BASE_URL: Optional[str] = None
    EMBEDDING_MODEL: Optional[str] = None

    # Mistral AI (TTS Voxtral, embeddings, and chat)
    # Get your key at https://console.mistral.ai
    MISTRAL_API_KEY: str = ""
    MISTRAL_BASE_URL: Optional[str] = None
    MISTRAL_EMBED_MODEL: str = "mistral-embed"
    MISTRAL_LLM_MODEL: str = "mistral-small-latest"
    MISTRAL_TTS_MODEL: str = "voxtral-mini-tts-2603"

    # CORS — comma-separated list of allowed origins
    CORS_ORIGINS: Union[List[str], str] = ["http://localhost:3000"]

    @field_validator("CORS_ORIGINS", mode="before")
    def _parse_cors(cls, v: Union[str, List[str]]) -> List[str]:
        if isinstance(v, str) and not v.startswith("["):
            return [i.strip() for i in v.split(",")]
        return v  # type: ignore[return-value]

    def get_effective_llm_provider(self) -> str:
        if self.LLM_PROVIDER:
            return self.LLM_PROVIDER.lower().strip()
        if self.MISTRAL_API_KEY:
            return "mistral"
        if self.GEMINI_API_KEY or self.GOOGLE_API_KEY:
            return "gemini"
        if self.OPENAI_API_KEY:
            return "openai"
        if self.DEEPSEEK_API_KEY:
            return "deepseek"
        return "mistral"

    def get_effective_llm_api_key(self) -> str:
        if self.LLM_API_KEY:
            return self.LLM_API_KEY
        provider = self.get_effective_llm_provider()
        if provider == "mistral":
            return self.MISTRAL_API_KEY or self.LLM_API_KEY
        if provider in {"gemini", "google"}:
            return self.GEMINI_API_KEY or self.GOOGLE_API_KEY or self.LLM_API_KEY
        if provider == "openai":
            return self.OPENAI_API_KEY or self.LLM_API_KEY
        if provider == "deepseek":
            return self.DEEPSEEK_API_KEY or self.LLM_API_KEY
        return (
            self.LLM_API_KEY
            or self.MISTRAL_API_KEY
            or self.GEMINI_API_KEY
            or self.GOOGLE_API_KEY
            or self.OPENAI_API_KEY
            or self.DEEPSEEK_API_KEY
        )

    def get_effective_llm_base_url(self) -> str:
        if self.LLM_BASE_URL:
            return self.LLM_BASE_URL
        provider = self.get_effective_llm_provider()
        defaults = {
            "mistral": "https://api.mistral.ai/v1",
            "gemini": "https://generativelanguage.googleapis.com/v1beta/openai/",
            "google": "https://generativelanguage.googleapis.com/v1beta/openai/",
            "openai": "https://api.openai.com/v1",
            "deepseek": "https://api.deepseek.com/v1",
            "ollama": "http://localhost:11434/v1",
            "openrouter": "https://openrouter.ai/api/v1",
            "groq": "https://api.groq.com/openai/v1",
        }
        if provider == "mistral" and self.MISTRAL_BASE_URL:
            return self.MISTRAL_BASE_URL
        if provider in {"gemini", "google"} and self.GEMINI_BASE_URL:
            return self.GEMINI_BASE_URL
        if provider == "openai" and self.OPENAI_BASE_URL:
            return self.OPENAI_BASE_URL
        if provider == "deepseek" and self.DEEPSEEK_BASE_URL:
            return self.DEEPSEEK_BASE_URL
        return defaults.get(provider, "https://api.mistral.ai/v1")

    def get_effective_llm_model(self) -> str:
        if self.LLM_MODEL:
            return self.LLM_MODEL
        provider = self.get_effective_llm_provider()
        defaults = {
            "mistral": self.MISTRAL_LLM_MODEL or "mistral-small-latest",
            "gemini": self.GEMINI_MODEL or "gemini-2.5-flash",
            "google": self.GEMINI_MODEL or "gemini-2.5-flash",
            "openai": self.OPENAI_MODEL or "gpt-4o-mini",
            "deepseek": self.DEEPSEEK_MODEL or "deepseek-chat",
            "ollama": "llama3.1",
            "openrouter": "mistralai/mistral-small-latest",
            "groq": "llama-3.3-70b-versatile",
        }
        return defaults.get(provider, self.MISTRAL_LLM_MODEL or "mistral-small-latest")

    def get_effective_embedding_provider(self) -> str:
        if self.EMBEDDING_PROVIDER:
            return self.EMBEDDING_PROVIDER.lower().strip()
        if self.MISTRAL_API_KEY:
            return "mistral"
        llm_provider = self.get_effective_llm_provider()
        if llm_provider == "mistral":
            return "mistral"
        if llm_provider in {"gemini", "google", "openai", "ollama", "custom"}:
            return llm_provider
        if self.GEMINI_API_KEY or self.GOOGLE_API_KEY:
            return "gemini"
        if self.OPENAI_API_KEY:
            return "openai"
        return "mistral"

    def get_effective_embedding_api_key(self) -> str:
        if self.EMBEDDING_API_KEY:
            return self.EMBEDDING_API_KEY
        provider = self.get_effective_embedding_provider()
        if provider == "mistral":
            return self.MISTRAL_API_KEY or self.LLM_API_KEY
        if provider in {"gemini", "google"}:
            return self.GEMINI_API_KEY or self.GOOGLE_API_KEY or self.LLM_API_KEY
        if provider == "openai":
            return self.OPENAI_API_KEY or self.LLM_API_KEY
        return (
            self.LLM_API_KEY
            or self.MISTRAL_API_KEY
            or self.GEMINI_API_KEY
            or self.GOOGLE_API_KEY
            or self.OPENAI_API_KEY
        )

    def get_effective_embedding_base_url(self) -> str:
        if self.EMBEDDING_BASE_URL:
            return self.EMBEDDING_BASE_URL
        provider = self.get_effective_embedding_provider()
        defaults = {
            "mistral": self.MISTRAL_BASE_URL or "https://api.mistral.ai/v1",
            "gemini": self.GEMINI_BASE_URL or "https://generativelanguage.googleapis.com/v1beta/openai/",
            "google": self.GEMINI_BASE_URL or "https://generativelanguage.googleapis.com/v1beta/openai/",
            "openai": self.OPENAI_BASE_URL or "https://api.openai.com/v1",
            "ollama": "http://localhost:11434/v1",
        }
        return defaults.get(provider, "https://api.mistral.ai/v1")

    def get_effective_embedding_model(self) -> str:
        if self.EMBEDDING_MODEL:
            return self.EMBEDDING_MODEL
        provider = self.get_effective_embedding_provider()
        defaults = {
            "mistral": self.MISTRAL_EMBED_MODEL or "mistral-embed",
            "gemini": "gemini-embedding-2",
            "google": "gemini-embedding-2",
            "openai": "text-embedding-3-small",
            "ollama": "nomic-embed-text",
        }
        return defaults.get(provider, self.MISTRAL_EMBED_MODEL or "mistral-embed")

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )


settings = Settings()
