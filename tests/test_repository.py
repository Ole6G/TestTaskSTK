from __future__ import annotations

from datetime import UTC, datetime

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from app.domain.entities import ProcessedNews
from app.infrastructure.persistence.models import Base, Cluster
from app.infrastructure.persistence.repositories import SqlAlchemyNewsRepository


def _session() -> Session:
    engine = create_engine("sqlite:///:memory:", future=True)
    Base.metadata.create_all(engine)
    session_factory = sessionmaker(bind=engine, autoflush=False, autocommit=False, future=True)
    return session_factory()


def _item(url: str, cluster_id: str, cluster_key: str) -> ProcessedNews:
    return ProcessedNews(
        source="src",
        url=url,
        published_at=datetime.now(UTC),
        title="title",
        body="body",
        company_name="company",
        location="moscow",
        industry="finance",
        cluster_id=cluster_id,
        cluster_key=cluster_key,
        sentiment_score=0.5,
        sentiment_rank=50,
        sentiment_label="positive",
        sentiment_confidence=0.8,
    )


def test_upsert_does_not_increment_cluster_count_for_same_url_update() -> None:
    session = _session()
    repo = SqlAlchemyNewsRepository(session)

    first = _item("https://example.com/1", "cl-a", "ck-a")
    second = _item("https://example.com/1", "cl-a", "ck-a")
    second.title = "updated title"

    repo.upsert_analyzed_items([first])
    repo.upsert_analyzed_items([second])

    cluster = session.get(Cluster, "cl-a")
    assert cluster is not None
    assert cluster.news_count == 1


def test_upsert_rebalances_cluster_counts_on_cluster_change() -> None:
    session = _session()
    repo = SqlAlchemyNewsRepository(session)

    repo.upsert_analyzed_items([_item("https://example.com/2", "cl-a", "ck-a")])
    repo.upsert_analyzed_items([_item("https://example.com/2", "cl-b", "ck-b")])

    cluster_a = session.get(Cluster, "cl-a")
    cluster_b = session.get(Cluster, "cl-b")
    assert cluster_a is not None and cluster_b is not None
    assert cluster_a.news_count == 0
    assert cluster_b.news_count == 1
