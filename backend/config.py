"""
Configuration settings for Agentic KB Factory.
Uses Pydantic Settings for environment variable management.
"""

from pydantic_settings import BaseSettings
from pydantic import Field
from typing import Optional
from functools import lru_cache


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""
    
    # Google Cloud Configuration
    gcp_project_id: str = Field(..., alias="GCP_PROJECT_ID")
    gcp_location: str = Field(default="us-central1", alias="GCP_LOCATION")
    firestore_database_id: str = Field(default="(default)", alias="FIRESTORE_DATABASE_ID")
    
    # Gemini API Configuration
    gemini_api_key: Optional[str] = Field(default=None, alias="GEMINI_API_KEY")
    google_genai_use_enterprise: bool = Field(default=False, alias="GOOGLE_GENAI_USE_ENTERPRISE")
    
    # Application Configuration
    app_name: str = Field(default="agentic-kb-factory", alias="APP_NAME")
    app_version: str = Field(default="1.0.0", alias="APP_VERSION")
    environment: str = Field(default="development", alias="ENVIRONMENT")
    debug: bool = Field(default=False, alias="DEBUG")
    
    # Cloud Run Configuration
    cloud_run_service: str = Field(default="agentic-kb-factory", alias="CLOUD_RUN_SERVICE")
    cloud_run_region: str = Field(default="us-central1", alias="CLOUD_RUN_REGION")
    
    # Pub/Sub Configuration
    pubsub_topic: str = Field(default="agent-jobs", alias="PUBSUB_TOPIC")
    
    # Agent Configuration
    collector_model: str = Field(default="gemini-3.5-flash")
    healer_model: str = Field(default="gemini-3.5-flash")
    healing_confidence_threshold: float = Field(default=0.8)
    max_healing_attempts: int = Field(default=3)
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False
        extra = "ignore"


@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()


# Export settings instance
settings = get_settings()
