from pydantic_settings import BaseSettings, SettingsConfigDict
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent


class Settings(BaseSettings):
    """
    Centralized configuration manager.
    Validates environment variables on application startup.
    """

    GOOGLE_API_KEY: str

    FRONTEND_URL: str = "http://localhost:5173"

    # Pydantic automatically casts "1", "true", or "yes" to True
    DEBUG_ON: bool = True

    SCANS_DIR: str = "scans"

    STORAGE_DIR: str = "logs"

    SUGGESTIONS_FILE: str = "agent_feature_suggestions.log"

    # Pydantic V2 configuration syntax
    model_config = SettingsConfigDict(
        env_file=str(BASE_DIR / ".env"),
        env_file_encoding="utf-8",
        extra="ignore",  # Ignores other vars in .env that are not defined here
    )

    # Log configuration
    LOG_LEVEL: str = "INFO"
    LOG_FILENAME: str = "app.log"


# Instantiate the settings so they are cached and ready to import anywhere
settings = Settings()
