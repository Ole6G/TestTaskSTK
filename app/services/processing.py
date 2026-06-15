"""Compatibility adapter for old import path."""

from app.application.services.news_analysis_service import analyze_news_batch
from app.domain.entities import ProcessedNews

__all__ = ["ProcessedNews", "analyze_news_batch"]
