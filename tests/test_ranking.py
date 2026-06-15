from app.services.ranking import SentimentRanker


def test_sentiment_ranker_positive_news() -> None:
    ranker = SentimentRanker(provider="local")
    result = ranker.analyze(
        title="Компания показала рост и рекорд прибыли",
        body="Это позитивный сигнал для инвесторов и стабильный прогноз.",
    )
    assert result.score > 0
    assert result.rank > 0
    assert result.label == "positive"
    assert 0 <= result.confidence <= 1


def test_sentiment_ranker_negative_news() -> None:
    ranker = SentimentRanker(provider="local")
    result = ranker.analyze(
        title="Компания получила штраф и убыток",
        body="Кризис усилил риски и привел к снижению показателей.",
    )
    assert result.score < 0
    assert result.rank < 0
    assert result.label == "negative"
    assert 0 <= result.confidence <= 1


def test_sentiment_ranker_neutral_news() -> None:
    ranker = SentimentRanker(provider="local")
    result = ranker.analyze(
        title="Компания провела презентацию новой стратегии",
        body="Руководство представило план на следующий год.",
    )
    assert result.score == 0
    assert result.rank == 0
    assert result.label == "neutral"
    assert 0 <= result.confidence <= 1


def test_sentiment_ranker_yandex_mode_falls_back_to_local_when_not_configured(monkeypatch) -> None:
    monkeypatch.delenv("YANDEX_API_KEY", raising=False)
    monkeypatch.delenv("YANDEX_FOLDER_ID", raising=False)
    monkeypatch.delenv("YANDEX_MODEL_URI", raising=False)
    monkeypatch.delenv("YANDEX_GPT_ENDPOINT", raising=False)
    ranker = SentimentRanker(provider="yandex")
    result = ranker.analyze(
        title="Компания показала рекорд прибыли",
        body="Рост и позитивный прогноз на следующий квартал.",
    )
    assert result.label == "positive"
    assert 0 <= result.confidence <= 1
