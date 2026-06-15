from __future__ import annotations

import csv
import io
import json
from datetime import datetime
from typing import Annotated, Any, Literal

from fastapi import APIRouter, Depends, File, Form, HTTPException, Query, UploadFile
from pydantic import ValidationError
from sqlalchemy.orm import Session

from app.application.services.news_analysis_service import NewsAnalysisService
from app.application.services.news_persistence_service import NewsPersistenceService
from app.domain.entities import ProcessedNews
from app.infrastructure.persistence.repositories import SqlAlchemyNewsRepository
from app.infrastructure.persistence.session import get_db
from app.presentation.api.schemas import AnalyzeResponse, NewsBatchRequest, NewsIn, NewsOut

router = APIRouter(prefix="/news", tags=["news"])
DbSession = Annotated[Session, Depends(get_db)]


def _to_response(analyzed_items: list[ProcessedNews]) -> AnalyzeResponse:
    clusters = {item.cluster_id for item in analyzed_items}
    return AnalyzeResponse(
        total_items=len(analyzed_items),
        cluster_count=len(clusters),
        items=[
            NewsOut(
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
            for item in analyzed_items
        ],
    )


def _parse_json_payload(content: bytes) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    try:
        payload = json.loads(content.decode("utf-8"))
    except json.JSONDecodeError as exc:
        raise HTTPException(status_code=400, detail=f"Invalid JSON file: {exc.msg}") from exc

    options: dict[str, Any] = {}
    if isinstance(payload, dict) and "items" in payload:
        items = payload["items"]
        for key in ("persist", "similarity_threshold", "sentiment_provider"):
            if key in payload:
                options[key] = payload[key]
    elif isinstance(payload, list):
        items = payload
    else:
        raise HTTPException(
            status_code=400, detail="JSON payload must be a list or object with 'items'."
        )

    if not isinstance(items, list):
        raise HTTPException(status_code=400, detail="'items' must be a list.")
    return items, options


def _parse_csv_payload(content: bytes) -> list[dict[str, Any]]:
    reader = csv.DictReader(io.StringIO(content.decode("utf-8")))
    required = {
        "source",
        "url",
        "published_at",
        "title",
        "body",
        "company_name",
        "location",
        "industry",
    }
    if not required.issubset(set(reader.fieldnames or [])):
        raise HTTPException(status_code=400, detail=f"CSV must contain columns: {sorted(required)}")

    items: list[dict[str, Any]] = []
    for row in reader:
        raw_ts = row["published_at"].strip()
        if raw_ts.endswith("Z"):
            raw_ts = raw_ts[:-1] + "+00:00"
        try:
            row["published_at"] = datetime.fromisoformat(raw_ts)
        except ValueError as exc:
            raise HTTPException(
                status_code=400, detail=f"Invalid CSV datetime '{row['published_at']}'"
            ) from exc
        items.append(row)
    return items


def _validate_news_items(raw_items: list[dict[str, Any]]) -> list[dict[str, Any]]:
    normalized: list[dict[str, Any]] = []
    errors: list[dict[str, Any]] = []

    for index, item in enumerate(raw_items):
        try:
            validated = NewsIn.model_validate(item)
            normalized.append(validated.model_dump())
        except ValidationError as exc:
            for error in exc.errors():
                errors.append(
                    {
                        "loc": ["items", index, *error.get("loc", ())],
                        "msg": error.get("msg", "Validation error"),
                        "type": error.get("type", "value_error"),
                    }
                )

    if errors:
        raise HTTPException(status_code=422, detail=errors)
    return normalized


@router.post("/analyze", response_model=AnalyzeResponse)
def analyze_news(request: NewsBatchRequest, db: DbSession) -> AnalyzeResponse:
    analysis_service = NewsAnalysisService(sentiment_provider=request.sentiment_provider)
    persistence_service = NewsPersistenceService(repository=SqlAlchemyNewsRepository(db))

    raw_items = [item.model_dump() for item in request.items]
    analyzed_items = analysis_service.analyze_batch(
        raw_items=raw_items,
        similarity_threshold=request.similarity_threshold,
    )

    if request.persist:
        persistence_service.persist(analyzed_items)

    return _to_response(analyzed_items)


@router.post("/analyze-file", response_model=AnalyzeResponse)
async def analyze_news_file(
    file: Annotated[UploadFile, File(...)],
    db: DbSession,
    persist: Annotated[bool | None, Form()] = None,
    similarity_threshold: Annotated[float | None, Form(ge=0.0, le=1.0)] = None,
    sentiment_provider: Annotated[Literal["auto", "local", "yandex"] | None, Form()] = None,
) -> AnalyzeResponse:
    content = await file.read()
    filename = file.filename or ""
    payload_options: dict[str, Any] = {}
    if filename.endswith(".json"):
        raw_items, payload_options = _parse_json_payload(content)
    elif filename.endswith(".csv"):
        raw_items = _parse_csv_payload(content)
    else:
        raise HTTPException(status_code=400, detail="Only .json and .csv files are supported.")

    raw_items = _validate_news_items(raw_items)

    effective_persist = payload_options.get("persist", True) if persist is None else persist
    effective_similarity_threshold = (
        payload_options.get("similarity_threshold", 0.72)
        if similarity_threshold is None
        else similarity_threshold
    )
    effective_sentiment_provider = (
        payload_options.get("sentiment_provider", "auto")
        if sentiment_provider is None
        else sentiment_provider
    )

    try:
        effective_similarity_threshold = float(effective_similarity_threshold)
    except (TypeError, ValueError) as exc:
        raise HTTPException(
            status_code=400, detail="similarity_threshold must be numeric."
        ) from exc
    if not (0.0 <= effective_similarity_threshold <= 1.0):
        raise HTTPException(status_code=422, detail="similarity_threshold must be between 0 and 1.")

    if effective_sentiment_provider not in {"auto", "local", "yandex"}:
        raise HTTPException(
            status_code=422, detail="sentiment_provider must be one of: auto, local, yandex."
        )
    if not isinstance(effective_persist, bool):
        raise HTTPException(status_code=422, detail="persist must be boolean.")

    analysis_service = NewsAnalysisService(sentiment_provider=effective_sentiment_provider)
    persistence_service = NewsPersistenceService(repository=SqlAlchemyNewsRepository(db))
    analyzed_items = analysis_service.analyze_batch(
        raw_items=raw_items,
        similarity_threshold=effective_similarity_threshold,
    )
    if effective_persist:
        persistence_service.persist(analyzed_items)

    return _to_response(analyzed_items)


@router.get("/clusters")
def list_clusters(
    db: DbSession,
    limit: Annotated[int, Query(ge=1, le=100)] = 20,
) -> list[dict[str, Any]]:
    persistence_service = NewsPersistenceService(repository=SqlAlchemyNewsRepository(db))
    rows = persistence_service.list_clusters(limit=limit)
    return [
        {
            "cluster_id": row.cluster_id,
            "company_name": row.company_name,
            "location": row.location,
            "industry": row.industry,
            "news_count": row.news_count,
            "avg_sentiment_score": row.avg_sentiment_score,
        }
        for row in rows
    ]
