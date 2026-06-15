"""Initial schema for news analysis service.

Revision ID: 20260615_01
Revises:
Create Date: 2026-06-15 11:00:00
"""

from __future__ import annotations

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision = "20260615_01"
down_revision = None
branch_labels = None
depends_on = None


def _create_clusters_table_if_missing(existing_tables: set[str]) -> None:
    if "clusters" in existing_tables:
        return

    op.create_table(
        "clusters",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("company_name", sa.String(length=255), nullable=False),
        sa.Column("location", sa.String(length=255), nullable=False),
        sa.Column("industry", sa.String(length=255), nullable=False),
        sa.Column("cluster_key", sa.String(length=255), nullable=False),
        sa.Column("centroid_ref", sa.Text(), nullable=True),
        sa.Column("news_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()
        ),
        sa.Column(
            "updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("cluster_key", name="uq_clusters_cluster_key"),
    )


def _create_news_items_table_if_missing(existing_tables: set[str]) -> None:
    if "news_items" in existing_tables:
        return

    op.create_table(
        "news_items",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("source", sa.String(length=255), nullable=False),
        sa.Column("url", sa.String(length=1024), nullable=False),
        sa.Column("published_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("title", sa.String(length=500), nullable=False),
        sa.Column("body", sa.Text(), nullable=False),
        sa.Column("company_name", sa.String(length=255), nullable=False),
        sa.Column("location", sa.String(length=255), nullable=False),
        sa.Column("industry", sa.String(length=255), nullable=False),
        sa.Column("sentiment_score", sa.Float(), nullable=False),
        sa.Column("sentiment_rank", sa.Integer(), nullable=True),
        sa.Column("sentiment_label", sa.String(length=32), nullable=False),
        sa.Column("sentiment_confidence", sa.Float(), nullable=True),
        sa.Column("cluster_id", sa.String(length=36), nullable=True),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()
        ),
        sa.ForeignKeyConstraint(["cluster_id"], ["clusters.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("url"),
    )


def _ensure_news_items_columns() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    if "news_items" not in inspector.get_table_names():
        return

    existing_columns = {column["name"] for column in inspector.get_columns("news_items")}
    if "sentiment_rank" not in existing_columns:
        op.add_column("news_items", sa.Column("sentiment_rank", sa.Integer(), nullable=True))
    if "sentiment_confidence" not in existing_columns:
        op.add_column("news_items", sa.Column("sentiment_confidence", sa.Float(), nullable=True))


def _ensure_news_items_indexes() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    if "news_items" not in inspector.get_table_names():
        return

    indexes = {index["name"] for index in inspector.get_indexes("news_items")}
    if "ix_news_items_published_at" not in indexes:
        op.create_index("ix_news_items_published_at", "news_items", ["published_at"], unique=False)
    if "ix_news_items_cluster_id" not in indexes:
        op.create_index("ix_news_items_cluster_id", "news_items", ["cluster_id"], unique=False)
    if "ix_news_items_company_location_industry" not in indexes:
        op.create_index(
            "ix_news_items_company_location_industry",
            "news_items",
            ["company_name", "location", "industry"],
            unique=False,
        )


def upgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    existing_tables = set(inspector.get_table_names())

    _create_clusters_table_if_missing(existing_tables)
    _create_news_items_table_if_missing(existing_tables)
    _ensure_news_items_columns()
    _ensure_news_items_indexes()


def downgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    existing_tables = set(inspector.get_table_names())

    if "news_items" in existing_tables:
        indexes = {index["name"] for index in inspector.get_indexes("news_items")}
        for index_name in (
            "ix_news_items_company_location_industry",
            "ix_news_items_cluster_id",
            "ix_news_items_published_at",
        ):
            if index_name in indexes:
                op.drop_index(index_name, table_name="news_items")
        op.drop_table("news_items")

    if "clusters" in existing_tables:
        op.drop_table("clusters")
