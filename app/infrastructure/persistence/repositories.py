from __future__ import annotations

from collections.abc import Sequence

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.domain.entities import ClusterSummary, ProcessedNews
from app.domain.ports import NewsRepository
from app.infrastructure.persistence.models import Cluster, NewsItem


class SqlAlchemyNewsRepository(NewsRepository):
    def __init__(self, db: Session) -> None:
        self.db = db

    def upsert_analyzed_items(self, analyzed_items: Sequence[ProcessedNews]) -> None:
        latest_by_url: dict[str, ProcessedNews] = {}
        for item in analyzed_items:
            latest_by_url[item.url] = item

        for item in latest_by_url.values():
            target_cluster = self.db.get(Cluster, item.cluster_id)
            if target_cluster is None:
                target_cluster = Cluster(
                    id=item.cluster_id,
                    company_name=item.company_name,
                    location=item.location,
                    industry=item.industry,
                    cluster_key=item.cluster_key,
                    centroid_ref=item.title[:500],
                    news_count=0,
                )
                self.db.add(target_cluster)

            existing_news = self.db.execute(
                select(NewsItem).where(NewsItem.url == item.url)
            ).scalar_one_or_none()
            if existing_news is None:
                target_cluster.news_count += 1
                self.db.add(
                    NewsItem(
                        source=item.source,
                        url=item.url,
                        published_at=item.published_at,
                        title=item.title,
                        body=item.body,
                        company_name=item.company_name,
                        location=item.location,
                        industry=item.industry,
                        cluster_id=item.cluster_id,
                        sentiment_score=item.sentiment_score,
                        sentiment_rank=item.sentiment_rank,
                        sentiment_label=item.sentiment_label,
                        sentiment_confidence=item.sentiment_confidence,
                    )
                )
                continue

            old_cluster_id = existing_news.cluster_id
            if old_cluster_id != item.cluster_id:
                if old_cluster_id:
                    old_cluster = self.db.get(Cluster, old_cluster_id)
                    if old_cluster is not None and old_cluster.news_count > 0:
                        old_cluster.news_count -= 1
                target_cluster.news_count += 1

            existing_news.source = item.source
            existing_news.published_at = item.published_at
            existing_news.title = item.title
            existing_news.body = item.body
            existing_news.company_name = item.company_name
            existing_news.location = item.location
            existing_news.industry = item.industry
            existing_news.cluster_id = item.cluster_id
            existing_news.sentiment_score = item.sentiment_score
            existing_news.sentiment_rank = item.sentiment_rank
            existing_news.sentiment_label = item.sentiment_label
            existing_news.sentiment_confidence = item.sentiment_confidence

        self.db.commit()

    def list_clusters(self, limit: int) -> list[ClusterSummary]:
        statement = (
            select(
                Cluster.id,
                Cluster.company_name,
                Cluster.location,
                Cluster.industry,
                Cluster.news_count,
                func.avg(NewsItem.sentiment_score).label("avg_sentiment_score"),
            )
            .join(NewsItem, NewsItem.cluster_id == Cluster.id, isouter=True)
            .group_by(Cluster.id)
            .order_by(Cluster.news_count.desc())
            .limit(limit)
        )
        rows = self.db.execute(statement).all()
        return [
            ClusterSummary(
                cluster_id=row.id,
                company_name=row.company_name,
                location=row.location,
                industry=row.industry,
                news_count=row.news_count,
                avg_sentiment_score=float(row.avg_sentiment_score)
                if row.avg_sentiment_score is not None
                else None,
            )
            for row in rows
        ]
