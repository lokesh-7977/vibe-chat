from functools import lru_cache
from pathlib import Path
from typing import Any

from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


def _find_env_file() -> str:
    """
    Prefer a .env file in the server folder; otherwise fall back to repo root.
    This allows running from either the repo root or `server/`.
    """
    current = Path(__file__).resolve()
    for parent in current.parents:
        candidate = parent / ".env"
        if candidate.exists():
            return str(candidate)
    return ".env"


class Settings(BaseSettings):
    app_name: str = "ContextOS Backend"
    app_version: str = "0.1.0"
    environment: str = "development"
    api_prefix: str = "/api/v1"
    debug: bool = True
    database_url: str
    secret_key: str = "change-me-before-production"
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 30
    refresh_token_expire_days: int = 7

    uploads_max_file_size_bytes: int = 50 * 1024 * 1024
    # Keep this as a simple string to avoid JSON parsing requirements for list env vars.
    # Use comma-separated values in env: UPLOADS_ALLOWED_MIME_TYPES=image/jpeg,image/png
    uploads_allowed_mime_types: str = (
        "application/pdf,"
        "application/msword,"
        "application/vnd.openxmlformats-officedocument.wordprocessingml.document,"
        "text/plain,"
        "text/markdown,"
        "image/jpeg,"
        "image/png,"
        "image/webp,"
        "image/gif,"
        "audio/mpeg,"
        "audio/mp4,"
        "audio/wav,"
        "audio/webm,"
        "audio/ogg"
    )

    cors_allow_origins: list[str] = []

    nvapi_api_key: str | None = None
    nvapi_base_url: str = "https://integrate.api.nvidia.com"
    nvapi_chat_model: str = "openai/gpt-oss-20b"

    embedding_api_key: str | None = None
    embedding_api_url: str | None = None
    embedding_model: str = "nvidia/nv-embed-qa-4"
    nvapi_translate_model: str = "nvidia/riva-translate-4b-instruct"
    nvapi_translate_fallback_model: str | None = None
    nvapi_vision_model: str = "meta/llama-3.2-11b-vision-instruct"

    rag_top_k: int = 8
    rag_max_sources_per_type: int = 50

    r2_endpoint_url: str | None = None
    r2_access_key_id: str | None = None
    r2_secret_access_key: str | None = None
    r2_bucket_name: str | None = None
    r2_public_base_url: str | None = None
    r2_presign_expires_seconds: int = 3600
    auth_rate_limit_window_seconds: int = 60
    auth_rate_limit_register_requests: int = 5
    auth_rate_limit_login_requests: int = 5
    auth_rate_limit_refresh_requests: int = 10
    auth_rate_limit_profile_requests: int = 30
    auth_rate_limit_delete_requests: int = 5
    auth_rate_limit_logout_requests: int = 10

    model_config = SettingsConfigDict(
        env_file=_find_env_file(),
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    @field_validator("debug", mode="before")
    @classmethod
    def normalize_debug(cls, value: Any) -> bool:
        if isinstance(value, bool):
            return value
        if value is None:
            return True
        normalized = str(value).strip().lower()
        if normalized in {"1", "true", "yes", "on", "debug", "development"}:
            return True
        if normalized in {"0", "false", "no", "off", "release", "prod", "production"}:
            return False
        return True

    @property
    def uploads_allowed_mime_types_list(self) -> list[str]:
        value = self.uploads_allowed_mime_types
        if value is None:
            return []
        if isinstance(value, str):
            # allow empty string
            return [part.strip() for part in value.split(",") if part.strip()]
        return [str(value).strip()] if str(value).strip() else []

    @field_validator("cors_allow_origins", mode="before")
    @classmethod
    def normalize_cors_allow_origins(cls, value: Any) -> list[str]:
        if value is None:
            return []
        if isinstance(value, str):
            return [part.strip() for part in value.split(",") if part.strip()]
        if isinstance(value, (list, tuple)):
            return [str(part).strip() for part in value if str(part).strip()]
        return [str(value).strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()
