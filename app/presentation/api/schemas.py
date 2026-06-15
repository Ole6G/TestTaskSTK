from __future__ import annotations

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field, HttpUrl


class NewsIn(BaseModel):
    source: str = Field(min_length=1, max_length=255)
    url: HttpUrl
    published_at: datetime
    title: str = Field(min_length=1, max_length=500)
    body: str = Field(min_length=1)
    company_name: str = Field(min_length=1, max_length=255)
    location: str = Field(min_length=1, max_length=255)
    industry: str = Field(min_length=1, max_length=255)


class NewsBatchRequest(BaseModel):
    items: list[NewsIn]
    persist: bool = True
    similarity_threshold: float = Field(default=0.72, ge=0.0, le=1.0)
    sentiment_provider: Literal["auto", "local", "yandex"] = "auto"


class NewsOut(BaseModel):
    source: str
    url: str
    published_at: datetime
    title: str
    body: str
    company_name: str
    location: str
    industry: str
    cluster_id: str
    sentiment_score: float
    sentiment_rank: int
    sentiment_label: str
    sentiment_confidence: float


class AnalyzeResponse(BaseModel):
    total_items: int
    cluster_count: int
    items: list[NewsOut]
