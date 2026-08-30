"""
Database setup: engine, session factory, and declarative base.

Every request gets its own SQLAlchemy Session via the `get_db`
dependency, which is closed automatically once the request finishes.

pg8000 quirk: unlike psycopg2/psycopg, pg8000 does not accept
libpq-style connection URL query parameters at all. Hosted Postgres
providers (Neon, Supabase, Railway, etc.) commonly hand out URLs
with several of these appended -- `sslmode=require`,
`channel_binding=require`, and others -- and each one raises its own
`TypeError: connect() got an unexpected keyword argument '...'` if
passed straight through. Rather than stripping them one at a time as
they turn up, drop the query string entirely for pg8000 URLs and
configure SSL the one way pg8000 actually wants it: via
`connect_args={"ssl_context": ...}`.
"""
import ssl
from urllib.parse import urlparse, urlunparse, parse_qsl

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

from app.config import settings


def _build_engine(database_url: str):
    parsed = urlparse(database_url)

    # Only postgres+pg8000 needs this treatment. Other URLs
    # (e.g. sqlite:///./test.db) have formats that don't round-trip
    # cleanly through urlparse/urlunparse, so leave them untouched.
    if "pg8000" not in parsed.scheme:
        return create_engine(database_url, pool_pre_ping=True)

    query_params = dict(parse_qsl(parsed.query))
    sslmode = query_params.get("sslmode")

    # Drop the entire query string -- pg8000 doesn't accept any of
    # these libpq-style params (sslmode, channel_binding, etc.) as
    # connect() keyword arguments.
    clean_url = urlunparse(parsed._replace(query=""))

    connect_args = {}
    # Hosted providers that need sslmode/channel_binding at all
    # virtually always require an encrypted connection, so default to
    # enabling SSL unless the URL explicitly said "disable".
    if sslmode != "disable":
        connect_args["ssl_context"] = ssl.create_default_context()

    return create_engine(clean_url, pool_pre_ping=True, connect_args=connect_args)


engine = _build_engine(settings.database_url)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()


def get_db():
    """FastAPI dependency that yields a DB session and always closes it."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()