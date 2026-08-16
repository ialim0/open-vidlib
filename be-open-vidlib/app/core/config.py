from typing import List, Union
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import field_validator


class Settings(BaseSettings):
    PROJECT_NAME: str = "GandaLab API"
    VERSION: str = "1.0.0"
    API_V1_PREFIX: str = "/api/v1"

    # PostgreSQL + pgvector
    DATABASE_URL: str = "postgresql://postgres:postgres@localhost:5432/gandalab"

    # Mistral AI
    # Get your key at https://console.mistral.ai
    MISTRAL_API_KEY: str = ""
    MISTRAL_EMBED_MODEL: str = "mistral-embed"
    MISTRAL_LLM_MODEL: str = "mistral-large-latest"
    MISTRAL_TTS_MODEL: str = "voxtral-mini-tts-2603"

    # CORS — comma-separated list of allowed origins
    CORS_ORIGINS: Union[List[str], str] = ["http://localhost:3000"]

    @field_validator("CORS_ORIGINS", mode="before")
    def _parse_cors(cls, v: Union[str, List[str]]) -> List[str]:
        if isinstance(v, str) and not v.startswith("["):
            return [i.strip() for i in v.split(",")]
        return v  # type: ignore[return-value]

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )


settings = Settings()
