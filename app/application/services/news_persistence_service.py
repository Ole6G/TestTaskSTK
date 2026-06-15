from __future__ import annotations

from collections.abc import Sequence

from app.domain.entities import ClusterSummary, ProcessedNews
from app.domain.ports import NewsRepository


class NewsPersistenceService:
    def __init__(self, repository: NewsRepository) -> None:
        self.repository = repository

    def persist(self, analyzed_items: Sequence[ProcessedNews]) -> None:
        if not analyzed_items:
            return
        self.repository.upsert_analyzed_items(analyzed_items)

    def list_clusters(self, limit: int) -> list[ClusterSummary]:
        return self.repository.list_clusters(limit=limit)
