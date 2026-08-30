"""
Centralized app configuration.

Reads settings from environment variables / a .env file so nothing
sensitive (like DB credentials) is hardcoded into the source.

database_url has NO default and no `os.getenv()` fallback on
purpose: pydantic-settings already reads a `DATABASE_URL` env var
(or `.env` entry) for a field named `database_url` automatically, so
adding `os.getenv()` is redundant. Worse, `os.getenv("DATABASE_URL")`
returns None if the var isn't set, and since Pydantic doesn't
validate default values, that None would pass through silently and
only fail later with a confusing error deep in SQLAlchemy. Leaving
this field required means a missing DATABASE_URL fails immediately,
at startup, with a clear "field required" error instead.
"""
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    database_url: str
    cors_origins: list[str] = ["*"]

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")


settings = Settings()
