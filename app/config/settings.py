from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    """Application settings loaded from environment variables."""
    model_config = SettingsConfigDict(env_file=".env")
    
    # LLM and KB configuration    
    kb_url: str = Field(..., alias="KB_URL")
    llm_provider: str = Field("gemini", alias="LLM_PROVIDER")
    llm_model: str = Field("gemini-2.5-flash", alias="LLM_MODEL")
    llm_api_key: str = Field("", alias="LLM_API_KEY")
    llm_base_url: str = Field("", alias="LLM_BASE_URL")

    # Retrieval and validation tuning
    max_message_chars: int = Field(4000, alias="MAX_MESSAGE_CHARS")
    min_section_score: int = Field(1, alias="MIN_SECTION_SCORE")
    max_context_sections: int = Field(3, alias="MAX_CONTEXT_SECTIONS")
    kb_timeout_seconds: float = Field(10.0, alias="KB_TIMEOUT_SECONDS")
    llm_timeout_seconds: float = Field(30.0, alias="LLM_TIMEOUT_SECONDS")
    
    # Logging configuration
    log_level: str = Field("INFO", alias="LOG_LEVEL")

    # Optional memory store configuration
    memory_store: str = Field("", alias="MEMORY_STORE")

    # Server configuration
    host: str = Field("0.0.0.0", alias="HOST")
    port: int = Field(8000, alias="PORT")

settings = Settings()