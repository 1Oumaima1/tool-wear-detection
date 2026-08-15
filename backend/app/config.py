from pathlib import Path
from pydantic_settings import BaseSettings, SettingsConfigDict

BASE_DIR = Path(__file__).resolve().parent.parent


class Settings(BaseSettings):
    # --- App ---
    APP_NAME: str = "Agatronic Industrial AI Monitoring Platform"
    ENV: str = "development"
    DEBUG: bool = True

    # --- Database ---
    DATABASE_URL: str = "postgresql+psycopg2://postgres:123@localhost:5432/tool_db"

    # --- JWT / Auth ---
    JWT_SECRET_KEY: str = "CHANGE_ME_IN_PRODUCTION"
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 8  # 8h

    # --- AI Model ---
    MODEL_PATH: str = str(BASE_DIR / "models" / "final_model.keras")
    IMG_SIZE: int = 224
    CLASS_NAMES: list[str] = ["dulled", "sharp", "used"]
    USE_TTA: bool = True
    TTA_ROUNDS: int = 5

    # --- Video / Live monitoring ---
    VIDEO_FOLDER: str = str(BASE_DIR / "videos")
    DEFAULT_FRAME_INTERVAL_SECONDS: float = 2.0

    # --- Decision engine defaults (overridable via /settings API, stored in DB) ---
    DEFAULT_CONFIDENCE_THRESHOLD: float = 0.75
    DEFAULT_CONSECUTIVE_DETECTIONS: int = 3

    # --- SMTP / Email alerts ---
    SMTP_HOST: str = "smtp.gmail.com"
    SMTP_PORT: int = 587
    SMTP_USER: str = ""
    SMTP_PASSWORD: str = ""
    SMTP_USE_TLS: bool = True
    ALERT_EMAIL_FROM: str = "alerts@agatronic.com"
    ALERT_EMAIL_TO: str = ""

    # --- CORS ---
    CORS_ORIGINS: list[str] = ["http://localhost:5173", "http://localhost:3000"]

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")


settings = Settings()

print(settings.DATABASE_URL)