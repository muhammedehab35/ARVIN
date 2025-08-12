import os
from pydantic import BaseModel

try:
    from pydantic_settings import BaseSettings
except ImportError:
    from pydantic import BaseSettings

class Settings(BaseSettings):
    OPENAI_API_KEY: str = os.getenv("OPENAI_API_KEY", "")
    MODEL_NAME: str = "gpt-4o"
    SAMPLE_MIN_ROWS: int = 200
    SAMPLE_MAX_ROWS: int = 400
    MAX_FILE_BYTES: int = 10 * 1024 * 1024
    ALLOWED_ORIGINS: list[str] = [
        "http://localhost:8501",  
        "https://*.streamlit.app",  
    ]
    ENVIRONMENT: str = os.getenv("ENVIRONMENT", "production")
    PORT: int = int(os.getenv("PORT", 8000))

settings = Settings()