from functools import lru_cache
from pathlib import Path
from pydantic import Field

from pydantic_settings import BaseSettings, SettingsConfigDict



PROJECT_ROOT = Path(__file__).resolve().parents[3]
ENV_FILE = PROJECT_ROOT / ".env"


class Settings(BaseSettings):
    app_name: str = "bts-monitoring"
    app_env: str = "development"

    rule_update_channel: str = "bts:rule-updates"

    fire_smoke_model_name: str = "fire-smoke-detector"


    rule_engine_local_cache_ttl_seconds: int = Field(
        default=300,
        ge=10,
        le=3600,
    )

    app_debug: bool = False

    database_url: str
    redis_url: str

    jwt_secret: str
    admin_api_key: str

    object_storage_endpoint: str
    object_storage_access_key: str
    object_storage_secret_key: str
    object_storage_bucket: str = "bts-evidence"

    telegram_enabled: bool = False
    telegram_bot_token: str = ""
    telegram_chat_id: str = ""

    model_config = SettingsConfigDict(
        env_file=ENV_FILE,
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    fire_smoke_model_path: Path = Path(
        "models/fire_smoke_detector.onnx"
    )

    fire_smoke_model_version: str = "1.0.0"

    fire_smoke_confidence_threshold: float = 0.50

    fire_smoke_iou_threshold: float = 0.45

    fire_smoke_confidence_threshold: float = Field(
        default=0.50,
        ge=0,
        le=1,
    )

    fire_smoke_iou_threshold: float = Field(
        default=0.45,
        ge=0,
        le=1,
    )

    redis_url: str

    rule_cache_key_prefix: str = "bts:mission-rules"

    rule_cache_ttl_seconds: int = Field(
        default=3600,
        ge=60,
        le=86400,
    )

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )





@lru_cache
def get_settings() -> Settings:
    fire_smoke_model_name: str = "fire-smoke-detector"
    fire_smoke_model_version: str = "1.0.0"
    return Settings()