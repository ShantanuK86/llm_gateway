from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    PROJECT_NAME: str = "LLM Gateway"
    OPENAI_API_KEY: str = ""
    GEMINI_API_KEY: str = ""
    REDIS_URL: str = "redis://localhost:6379/0"
    DATABASE_URL: str = "postgresql+asyncpg://postgres:postgres@localhost:5432/llm_gateway"

    class Config:
        env_file = ".env"

settings = Settings()
