from __future__ import annotations

import hashlib
import math
import re
from collections import Counter, defaultdict
from collections.abc import Iterable, Sequence
from dataclasses import dataclass, field
from typing import Any

TOKEN_PATTERN = re.compile(r"[A-Za-zА-Яа-яЁё0-9]+")
STOPWORDS = {
    "и",
    "в",
    "на",
    "по",
    "к",
    "о",
    "с",
    "у",
    "за",
    "из",
    "для",
    "что",
    "как",
    "это",
    "the",
    "a",
    "an",
    "of",
    "to",
    "in",
    "on",
}


def normalize_attr(value: str) -> str:
    return " ".join(value.lower().strip().split())


def build_cluster_key(company_name: str, location: str, industry: str) -> str:
    normalized = (
        normalize_attr(company_name),
        normalize_attr(location),
        normalize_attr(industry),
    )
    return "::".join(normalized)


def tokenize(text: str) -> list[str]:
    tokens = TOKEN_PATTERN.findall(text.lower())
    return [token for token in tokens if token not in STOPWORDS]


def text_to_vector(title: str, body: str) -> Counter[str]:
    tokens = tokenize(f"{title} {body}")
    if not tokens:
        return Counter({"__empty__": 1})
    return Counter(tokens)


def cosine_similarity(left: Counter[str], right: Counter[str]) -> float:
    numerator = 0.0
    for term, value in left.items():
        numerator += value * right.get(term, 0.0)

    left_norm = math.sqrt(sum(value * value for value in left.values()))
    right_norm = math.sqrt(sum(value * value for value in right.values()))
    if left_norm == 0.0 or right_norm == 0.0:
        return 0.0
    return numerator / (left_norm * right_norm)


def _derive_cluster_id(base_key: str, ordinal: int) -> str:
    digest = hashlib.sha1(f"{base_key}:{ordinal}".encode()).hexdigest()[:16]
    return f"cl-{digest}"


@dataclass
class _Subcluster:
    cluster_id: str
    aggregate_vector: Counter[str] = field(default_factory=Counter)
    items_count: int = 0

    def similarity(self, vector: Counter[str]) -> float:
        return cosine_similarity(vector, self.aggregate_vector)

    def add(self, vector: Counter[str]) -> None:
        self.aggregate_vector.update(vector)
        self.items_count += 1


def cluster_news_items(
    items: Sequence[dict[str, Any]],
    similarity_threshold: float = 0.72,
) -> list[str]:
    """
    Cluster news in 2 steps:
    1) deterministic partition by company_name + location + industry
    2) near-duplicate grouping inside each partition using cosine similarity.
    """
    grouped_indexes: dict[str, list[int]] = defaultdict(list)
    for idx, item in enumerate(items):
        key = build_cluster_key(
            item["company_name"],
            item["location"],
            item["industry"],
        )
        grouped_indexes[key].append(idx)

    cluster_ids: list[str] = [""] * len(items)
    for base_key, indexes in grouped_indexes.items():
        subclusters: list[_Subcluster] = []
        for idx in indexes:
            vector = text_to_vector(items[idx]["title"], items[idx]["body"])

            best_match: _Subcluster | None = None
            best_score = -1.0
            for subcluster in subclusters:
                score = subcluster.similarity(vector)
                if score > best_score:
                    best_score = score
                    best_match = subcluster

            if best_match is not None and best_score >= similarity_threshold:
                best_match.add(vector)
                cluster_ids[idx] = best_match.cluster_id
                continue

            cluster_id = _derive_cluster_id(base_key, len(subclusters))
            new_subcluster = _Subcluster(cluster_id=cluster_id)
            new_subcluster.add(vector)
            subclusters.append(new_subcluster)
            cluster_ids[idx] = cluster_id

    return cluster_ids


def cluster_sizes(cluster_ids: Iterable[str]) -> dict[str, int]:
    counts: dict[str, int] = {}
    for cluster_id in cluster_ids:
        counts[cluster_id] = counts.get(cluster_id, 0) + 1
    return counts
