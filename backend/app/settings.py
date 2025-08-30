from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    # Default to Postgres via .env, but if not set, fall back to SQLite (dev/tests)
    DATABASE_URL: str = "sqlite:///./pychatx.db"

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"

settings = Settings()
