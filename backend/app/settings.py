from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    # SQLite for now. We'll switch to Postgres in the next task.
    DATABASE_URL: str = "sqlite:///./pychatx.db"

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"

settings = Settings()
