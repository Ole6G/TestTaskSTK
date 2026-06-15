from datetime import UTC, datetime

from fastapi.testclient import TestClient

from app.main import app


def test_analyze_endpoint_returns_clusters_and_sentiment() -> None:
    client = TestClient(app)
    payload = {
        "persist": False,
        "sentiment_provider": "local",
        "similarity_threshold": 0.5,
        "items": [
            {
                "source": "rbc",
                "url": "https://example.com/news-1",
                "published_at": datetime.now(UTC).isoformat(),
                "title": "Газпром увеличил прибыль",
                "body": "Компания показала рост прибыли в отчете.",
                "company_name": "Газпром",
                "location": "Москва",
                "industry": "Энергетика",
            },
            {
                "source": "vedomosti",
                "url": "https://example.com/news-2",
                "published_at": datetime.now(UTC).isoformat(),
                "title": "Газпром получил штраф",
                "body": "Регулятор зафиксировал нарушение и выписал штраф.",
                "company_name": "Газпром",
                "location": "Москва",
                "industry": "Энергетика",
            },
        ],
    }

    response = client.post("/api/news/analyze", json=payload)
    assert response.status_code == 200
    body = response.json()

    assert body["total_items"] == 2
    assert body["cluster_count"] >= 1
    assert len(body["items"]) == 2
    assert all(
        item["sentiment_label"] in {"negative", "neutral", "positive"} for item in body["items"]
    )
    assert all(0 <= item["sentiment_confidence"] <= 1 for item in body["items"])


def test_clusters_endpoint() -> None:
    client = TestClient(app)
    response = client.get("/api/news/clusters")
    assert response.status_code == 200
    assert isinstance(response.json(), list)


def test_analyze_file_json_uses_payload_options() -> None:
    client = TestClient(app)
    payload = {
        "persist": False,
        "similarity_threshold": 0.4,
        "sentiment_provider": "local",
        "items": [
            {
                "source": "rbc",
                "url": "https://example.com/file-news-1",
                "published_at": datetime.now(UTC).isoformat(),
                "title": "Компания показала рост прибыли",
                "body": "Рост и прибыль поддерживают позитивную динамику.",
                "company_name": "Компания",
                "location": "Москва",
                "industry": "Финансы",
            }
        ],
    }
    files = {"file": ("payload.json", json_bytes(payload), "application/json")}
    response = client.post("/api/news/analyze-file", files=files)
    assert response.status_code == 200
    body = response.json()
    assert body["total_items"] == 1
    assert body["items"][0]["sentiment_label"] in {"negative", "neutral", "positive"}


def json_bytes(payload: dict) -> bytes:
    import json

    return json.dumps(payload).encode("utf-8")
