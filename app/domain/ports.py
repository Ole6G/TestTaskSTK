from __future__ import annotations

from collections.abc import Sequence
from typing import Protocol

from app.domain.entities import ClusterSummary, ProcessedNews


class NewsRepository(Protocol):
    def upsert_analyzed_items(self, analyzed_items: Sequence[ProcessedNews]) -> None: ...

    def list_clusters(self, limit: int) -> list[ClusterSummary]: ...
