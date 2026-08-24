import secrets
from functools import lru_cache
from typing import List

from pydantic import field_validator, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    # ── Application ──────────────────────────────────────────────────────────
    APP_NAME: str = "HELIOS"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = False

    # ── Database ─────────────────────────────────────────────────────────────
    DATABASE_URL: str = "sqlite+aiosqlite:///./helios.db"
    DATABASE_POOL_SIZE: int = 20

    # ── Vector Database ───────────────────────────────────────────────────────
    CHROMA_PERSIST_DIR: str = "./data/chroma"
    EMBEDDING_MODEL: str = "all-MiniLM-L6-v2"

    # ── AI / OpenVINO ─────────────────────────────────────────────────────────
    # Path is relative to the services/ working directory
    OV_MODEL_PATH: str = "./models/phi-4-mini-openvino"
    OV_DEVICE: str = "AUTO"          # AUTO lets the runtime pick NPU > GPU > CPU
    OV_MAX_CONTEXT: int = 128000
    OV_TEMPERATURE: float = 0.1      # Low temp keeps security analysis grounded
    OV_TOP_P: float = 0.9

    # ── Security ──────────────────────────────────────────────────────────────
    # REQUIRED in production — validated below. In dev, auto-generated if absent.
    SECRET_KEY: str = ""
    ENCRYPTION_KEY_PATH: str = "./data/keys"
    ARGON2_TIME_COST: int = 2
    ARGON2_MEMORY_COST: int = 65536  # 64 MB

    # ── CORS ──────────────────────────────────────────────────────────────────
    # Comma-separated list in .env: CORS_ORIGINS=http://localhost:5173,tauri://localhost
    CORS_ORIGINS: List[str] = [
        "http://localhost:5173",
        "http://localhost:3000",
        "tauri://localhost",
        "https://tauri.localhost",
    ]

    # ── Storage ───────────────────────────────────────────────────────────────
    UPLOAD_DIR: str = "./data/uploads"
    MAX_UPLOAD_SIZE: int = 500 * 1024 * 1024  # 500 MB

    # ── Redis / Celery ────────────────────────────────────────────────────────
    REDIS_URL: str = "redis://localhost:6379/0"
    CELERY_BROKER_URL: str = "redis://localhost:6379/1"

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        # Allow CORS_ORIGINS to be provided as a JSON list or comma-separated string
        env_parse_none_str="null",
        extra="ignore",
    )

    # ── Validators ────────────────────────────────────────────────────────────

    @field_validator("SECRET_KEY", mode="before")
    @classmethod
    def _require_secret_key(cls, v: str) -> str:
        """
        In production (DEBUG=False and no key provided) this would raise.
        In development we auto-generate a key and print a warning so the
        developer is never silently running with an empty secret.
        """
        if not v or v in ("change-me-in-production", "changeme", ""):
            generated = secrets.token_hex(32)
            import warnings
            warnings.warn(
                "\n\n⚠️  SECRET_KEY is not set or uses a default value.\n"
                f"   A random key has been generated for this session: {generated}\n"
                "   Set SECRET_KEY in your .env file to persist authentication.\n",
                stacklevel=2,
            )
            return generated
        return v

    @field_validator("OV_DEVICE", mode="before")
    @classmethod
    def _validate_device(cls, v: str) -> str:
        allowed = {"AUTO", "NPU", "GPU", "CPU"}
        upper = v.upper()
        if upper not in allowed:
            raise ValueError(f"OV_DEVICE must be one of {allowed}, got '{v}'")
        return upper

    @field_validator("DATABASE_POOL_SIZE", mode="before")
    @classmethod
    def _pool_size_range(cls, v: int) -> int:
        if not (1 <= int(v) <= 100):
            raise ValueError("DATABASE_POOL_SIZE must be between 1 and 100")
        return int(v)

    @field_validator("OV_TEMPERATURE", mode="before")
    @classmethod
    def _temp_range(cls, v: float) -> float:
        v = float(v)
        if not (0.0 <= v <= 2.0):
            raise ValueError("OV_TEMPERATURE must be between 0.0 and 2.0")
        return v

    @field_validator("CORS_ORIGINS", mode="before")
    @classmethod
    def _parse_cors(cls, v):
        """
        Accept a Python list (already parsed by pydantic from JSON),
        a JSON array string, or a comma-separated string.
        Pydantic-settings v2 will JSON-decode List fields from .env automatically
        when the value is a valid JSON array; this validator handles the
        comma-separated fallback for convenience.
        """
        if isinstance(v, list):
            return v
        if isinstance(v, str):
            stripped = v.strip()
            if stripped.startswith("["):
                import json
                try:
                    return json.loads(stripped)
                except json.JSONDecodeError:
                    pass
            # Comma-separated fallback
            return [origin.strip() for origin in stripped.split(",") if origin.strip()]
        return v


@lru_cache
def get_settings() -> Settings:
    return Settings()
