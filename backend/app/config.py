# app/config.py
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    APP_NAME: str = "whatsap"
    DEBUG: bool = False

    # Database (default to sqlite so dev runs out of the box)
    DATABASE_URL: str = "sqlite+aiosqlite:///./test.db"

    # Upload folder used by app/api/uploads.py
    UPLOAD_DIR: str = "./uploads"

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
    )

settings = Settings()
