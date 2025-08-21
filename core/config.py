import os
from typing import Optional
from pydantic_settings import BaseSettings
from dotenv import load_dotenv

load_dotenv()

class Settings(BaseSettings):
    # OpenAI
    openai_api_key: str = os.getenv("OPENAI_API_KEY", "")
    default_model: str = "gpt-4o"
    fallback_model: str = "gpt-3.5-turbo"
    temperature: float = 0.1
    max_retries: int = 3
    
    # Aplicação
    app_name: str = "SlideTranslator Pro"
    debug: bool = False
    
    class Config:
        env_file = ".env"
        case_sensitive = False

settings = Settings()
