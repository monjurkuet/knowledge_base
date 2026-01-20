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
    openai_api_base: str = Field(default="http://localhost:8317/v1")
    max_retries: int = Field(default=3)
    timeout: int = Field(default=120)


class APIConfig(BaseModel):
    """API server configuration"""

    host: str = Field(default_factory=lambda: os.getenv("API_HOST", "0.0.0.0"))
    port: int = Field(
        default_factory=lambda: int(os.getenv("API_PORT", "8000")),
        ge=1,
        le=65535,
    )
    cors_origins: list[str] = Field(default_factory=lambda: ["*"])
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


class ProcessingConfig(BaseModel):
    """Batch processing configuration"""

    embedding_batch_size: int = Field(
        default_factory=lambda: int(os.getenv("EMBEDDING_BATCH_SIZE", "50")),
        description="Number of entities to process per embedding batch",
        gt=0,
    )
    summarization_batch_size: int = Field(
        default_factory=lambda: int(os.getenv("SUMMARIZATION_BATCH_SIZE", "5")),
        description="Number of communities to summarize per batch",
    )
    graph_page_size: int = Field(
        default_factory=lambda: int(os.getenv("GRAPH_PAGE_SIZE", "10000")),
        description="Number of nodes/edges to load per graph page",
    )


class Config(BaseModel):
    """Main configuration class"""

    database: DatabaseConfig = Field(default_factory=DatabaseConfig)
    llm: LLMConfig = Field(default_factory=LLMConfig)
    api: APIConfig = Field(default_factory=APIConfig)
    streamlit: StreamlitConfig = Field(default_factory=StreamlitConfig)
    logging: LoggingConfig = Field(default_factory=LoggingConfig)
    processing: ProcessingConfig = Field(default_factory=ProcessingConfig)


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
