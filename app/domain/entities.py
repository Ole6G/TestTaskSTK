from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime


@dataclass
class ProcessedNews:
    source: str
    url: str
    published_at: datetime
    title: str
    body: str
    company_name: str
    location: str
    industry: str
    cluster_id: str
    cluster_key: str
    sentiment_score: float
    sentiment_rank: int
    sentiment_label: str
    sentiment_confidence: float


@dataclass
class ClusterSummary:
    cluster_id: str
    company_name: str
    location: str
    industry: str
    news_count: int
    avg_sentiment_score: float | None
