"""Compatibility adapter for old import path."""

from app.infrastructure.persistence.session import DATABASE_URL, SessionLocal, engine, get_db

__all__ = ["DATABASE_URL", "SessionLocal", "engine", "get_db"]
