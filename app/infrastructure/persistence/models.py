from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import (
    DateTime,
    Float,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    pass


class Cluster(Base):
    __tablename__ = "clusters"
    __table_args__ = (UniqueConstraint("cluster_key", name="uq_clusters_cluster_key"),)

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    company_name: Mapped[str] = mapped_column(String(255), nullable=False)
    location: Mapped[str] = mapped_column(String(255), nullable=False)
    industry: Mapped[str] = mapped_column(String(255), nullable=False)
    cluster_key: Mapped[str] = mapped_column(String(255), nullable=False)
    centroid_ref: Mapped[str | None] = mapped_column(Text, nullable=True)
    news_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    news_items: Mapped[list[NewsItem]] = relationship(back_populates="cluster")


class NewsItem(Base):
    __tablename__ = "news_items"
    __table_args__ = (
        Index("ix_news_items_published_at", "published_at"),
        Index("ix_news_items_cluster_id", "cluster_id"),
        Index("ix_news_items_company_location_industry", "company_name", "location", "industry"),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    source: Mapped[str] = mapped_column(String(255), nullable=False)
    url: Mapped[str] = mapped_column(String(1024), nullable=False, unique=True)
    published_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    title: Mapped[str] = mapped_column(String(500), nullable=False)
    body: Mapped[str] = mapped_column(Text, nullable=False)
    company_name: Mapped[str] = mapped_column(String(255), nullable=False)
    location: Mapped[str] = mapped_column(String(255), nullable=False)
    industry: Mapped[str] = mapped_column(String(255), nullable=False)
    sentiment_score: Mapped[float] = mapped_column(Float, nullable=False)
    sentiment_rank: Mapped[int | None] = mapped_column(Integer, nullable=True)
    sentiment_label: Mapped[str] = mapped_column(String(32), nullable=False)
    sentiment_confidence: Mapped[float | None] = mapped_column(Float, nullable=True)
    cluster_id: Mapped[str | None] = mapped_column(
        String(36), ForeignKey("clusters.id"), nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    cluster: Mapped[Cluster | None] = relationship(back_populates="news_items")
