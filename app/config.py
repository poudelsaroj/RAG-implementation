from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    gemini_api_key: str
    qdrant_api_key: str = ""
    qdrant_url: str = ""
    redis_url: str = "redis://localhost:6379"
    database_url: str = "sqlite:///./app.db"
    
    class Config:
        env_file = ".env"

settings = Settings()