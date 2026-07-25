"""AURA-EAGLE — Core Configuration"""
from pydantic_settings import BaseSettings
from pydantic import Field
import os


class Settings(BaseSettings):
    # Application
    app_name: str = "PROJECT AURA-EAGLE"
    app_version: str = "1.0.0"
    debug: bool = Field(default=False, env="DEBUG")
    environment: str = Field(default="development", env="ENVIRONMENT")

    # Server
    host: str = "0.0.0.0"
    port: int = 8000
    cors_origins: list[str] = ["*"]

    # Database
    database_url: str = Field(default="", env="DATABASE_URL")

    # Security
    session_secret: str = Field(default="aura-eagle-dev-secret", env="SESSION_SECRET")
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 60

    # Agent System
    confidence_threshold: float = 0.65
    ethical_threshold: float = 0.5
    simulation_depth: int = 5
    max_agent_iterations: int = 10

    # Memory
    sensory_ttl_seconds: int = 30
    working_memory_size: int = 50
    episodic_memory_max: int = 10000

    # AURA Score weights
    intelligence_weight: float = 0.4
    adaptation_weight: float = 0.3
    reliability_weight: float = 0.3

    class Config:
        env_file = ".env"
        extra = "ignore"


settings = Settings()
