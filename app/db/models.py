"""Compatibility adapter for old import path."""

from app.infrastructure.persistence.models import Base, Cluster, NewsItem

__all__ = ["Base", "Cluster", "NewsItem"]
