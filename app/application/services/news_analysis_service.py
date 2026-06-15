from __future__ import annotations

import hashlib
from typing import Any

from app.domain.entities import ProcessedNews
from app.domain.services.clustering import build_cluster_key, cluster_news_items, normalize_attr
from app.domain.services.sentiment import SentimentProvider, SentimentRanker


class NewsAnalysisService:
    def __init__(self, sentiment_provider: SentimentProvider = "auto") -> None:
        self.ranker = SentimentRanker(provider=sentiment_provider)

    @staticmethod
    def normalize_news_payload(item: dict[str, Any]) -> dict[str, Any]:
        normalized = dict(item)
        normalized["source"] = normalize_attr(str(item["source"]))
        normalized["title"] = " ".join(str(item["title"]).split())
        normalized["body"] = " ".join(str(item["body"]).split())
        normalized["company_name"] = normalize_attr(str(item["company_name"]))
        normalized["location"] = normalize_attr(str(item["location"]))
        normalized["industry"] = normalize_attr(str(item["industry"]))
        normalized["url"] = str(item["url"]).strip()
        return normalized

    @staticmethod
    def build_storage_cluster_key(
        company_name: str,
        location: str,
        industry: str,
        cluster_id: str,
    ) -> str:
        raw_key = f"{build_cluster_key(company_name, location, industry)}::{cluster_id}"
        digest = hashlib.sha1(raw_key.encode("utf-8")).hexdigest()
        return f"ck-{digest}"

    def analyze_batch(
        self,
        raw_items: list[dict[str, Any]],
        similarity_threshold: float = 0.72,
    ) -> list[ProcessedNews]:
        normalized_items = [self.normalize_news_payload(item) for item in raw_items]
        cluster_ids = cluster_news_items(
            normalized_items, similarity_threshold=similarity_threshold
        )

        output: list[ProcessedNews] = []
        for item, cluster_id in zip(normalized_items, cluster_ids, strict=True):
            sentiment = self.ranker.analyze(item["title"], item["body"])
            output.append(
                ProcessedNews(
                    source=item["source"],
                    url=item["url"],
                    published_at=item["published_at"],
                    title=item["title"],
                    body=item["body"],
                    company_name=item["company_name"],
                    location=item["location"],
                    industry=item["industry"],
                    cluster_id=cluster_id,
                    cluster_key=self.build_storage_cluster_key(
                        company_name=item["company_name"],
                        location=item["location"],
                        industry=item["industry"],
                        cluster_id=cluster_id,
                    ),
                    sentiment_score=sentiment.score,
                    sentiment_rank=sentiment.rank,
                    sentiment_label=sentiment.label,
                    sentiment_confidence=sentiment.confidence,
                )
            )
        return output


def analyze_news_batch(
    raw_items: list[dict[str, Any]],
    similarity_threshold: float = 0.72,
    sentiment_provider: SentimentProvider = "auto",
) -> list[ProcessedNews]:
    service = NewsAnalysisService(sentiment_provider=sentiment_provider)
    return service.analyze_batch(raw_items=raw_items, similarity_threshold=similarity_threshold)
