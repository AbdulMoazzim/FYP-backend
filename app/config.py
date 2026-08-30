"""
Centralized app configuration.

Reads settings from environment variables / a .env file so nothing
sensitive (like DB credentials) is hardcoded into the source.
"""
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    database_url: str = "postgresql+pg8000://postgres:postgres@localhost:5432/fyp_platform"

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")


settings = Settings()
