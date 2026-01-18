"""
Configuration management for the Knowledge Base GraphRAG system
"""

import os

from dotenv import load_dotenv
from pydantic import BaseModel, Field

load_dotenv()


class DatabaseConfig(BaseModel):
    """Database configuration"""

    user: str = Field(default_factory=lambda: os.getenv("DB_USER", "postgres"))
    password: str = Field(default_factory=lambda: os.getenv("DB_PASSWORD", ""))
    host: str = Field(default_factory=lambda: os.getenv("DB_HOST", "localhost"))
    port: int = Field(default_factory=lambda: int(os.getenv("DB_PORT", "5432")))
    name: str = Field(default_factory=lambda: os.getenv("DB_NAME", "knowledge_base"))

    @property
    def connection_string(self) -> str:
        """Generate PostgreSQL connection string"""
        return f"postgresql://{self.user}:{self.password}@{self.host}:{self.port}/{self.name}"


class LLMConfig(BaseModel):
    """LLM configuration"""

    provider: str = Field(default_factory=lambda: os.getenv("LLM_PROVIDER", "openai"))
    model_name: str = Field(
        default_factory=lambda: os.getenv("LLM_MODEL", "gemini-2.5-flash-lite")
    )
    api_key: str | None = Field(
        default_factory=lambda: os.getenv("OPENAI_API_KEY", "not-required")
    )
    google_api_key: str | None = Field(
        default_factory=lambda: os.getenv("GOOGLE_API_KEY", None)
    )
    openai_api_base: str = Field(default="http://localhost:8317/v1")
    max_retries: int = Field(default=3)
    timeout: int = Field(default=120)
    max_tokens: int = Field(default=3000)
    temperature: float = Field(default=0.1)
    extract_max_tokens: int = Field(default=3000)
    extract_temperature: float = Field(default=0.1)
    summarize_max_tokens: int = Field(default=3000)
    summarize_temperature: float = Field(default=0.1)


class APIConfig(BaseModel):
    """API server configuration"""

    host: str = Field(default_factory=lambda: os.getenv("API_HOST", "0.0.0.0"))
    port: int = Field(default_factory=lambda: int(os.getenv("API_PORT", "8000")))
    cors_origins: list = Field(default_factory=lambda: ["*"])
    reload: bool = Field(
        default_factory=lambda: os.getenv("API_RELOAD", "false").lower() == "true"
    )


class StreamlitConfig(BaseModel):
    """Streamlit UI configuration"""

    api_base_url: str = Field(
        default_factory=lambda: os.getenv("STREAMLIT_API_URL", "http://localhost:8000")
    )
    ws_url: str = Field(
        default_factory=lambda: os.getenv("STREAMLIT_WS_URL", "ws://localhost:8000/ws")
    )


class LoggingConfig(BaseModel):
    """Logging configuration"""

    level: str = Field(default_factory=lambda: os.getenv("LOG_LEVEL", "INFO"))
    format: str = Field(
        default_factory=lambda: os.getenv(
            "LOG_FORMAT", "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
        )
    )


class Config(BaseModel):
    """Main configuration class"""

    database: DatabaseConfig = Field(default_factory=DatabaseConfig)
    llm: LLMConfig = Field(default_factory=LLMConfig)
    api: APIConfig = Field(default_factory=APIConfig)
    streamlit: StreamlitConfig = Field(default_factory=StreamlitConfig)
    logging: LoggingConfig = Field(default_factory=LoggingConfig)


config = Config()


def get_config() -> Config:
    """Get the global configuration instance"""
    return config


def reload_config() -> Config:
    """Reload configuration from environment variables"""
    global config
    load_dotenv(override=True)
    config = Config()
    return config
