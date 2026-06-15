"""Compatibility adapter for old import path."""

from app.domain.services.clustering import (  # noqa: F401
    build_cluster_key,
    cluster_news_items,
    cluster_sizes,
    cosine_similarity,
    normalize_attr,
    text_to_vector,
    tokenize,
)

__all__ = [
    "build_cluster_key",
    "cluster_news_items",
    "cluster_sizes",
    "cosine_similarity",
    "normalize_attr",
    "text_to_vector",
    "tokenize",
]
