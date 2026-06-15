from __future__ import annotations

import json
import os
import re
from dataclasses import dataclass
from typing import Literal

import httpx

TOKEN_PATTERN = re.compile(r"[A-Za-zА-Яа-яЁё0-9]+")

POSITIVE_WORDS = {
    "рост",
    "прибыль",
    "улучшение",
    "успех",
    "рекорд",
    "стабильный",
    "выиграл",
    "развитие",
    "оптимистичный",
    "increase",
    "profit",
    "growth",
    "strong",
    "positive",
}

NEGATIVE_WORDS = {
    "падение",
    "убыток",
    "штраф",
    "кризис",
    "снижение",
    "срыв",
    "проблема",
    "негатив",
    "долг",
    "loss",
    "drop",
    "decline",
    "risk",
    "negative",
}

NEGATIONS = {"не", "нет", "without", "no", "not"}
INTENSIFIERS = {"очень", "сильно", "значительно", "резко", "very", "strongly", "sharply"}
DAMPENERS = {"слегка", "умеренно", "частично", "somewhat", "slightly", "partly"}


def _tokenize(text: str) -> list[str]:
    return TOKEN_PATTERN.findall(text.lower())


@dataclass
class SentimentResult:
    score: float
    rank: int
    label: str
    confidence: float


def _score_to_label(score: float) -> str:
    if score > 0.2:
        return "positive"
    if score < -0.2:
        return "negative"
    return "neutral"


def _normalize_confidence(confidence: float) -> float:
    return max(0.0, min(1.0, confidence))


def _build_result(score: float, confidence: float) -> SentimentResult:
    clipped_score = max(-1.0, min(1.0, score))
    return SentimentResult(
        score=clipped_score,
        rank=int(round(clipped_score * 100)),
        label=_score_to_label(clipped_score),
        confidence=_normalize_confidence(confidence),
    )


class LexiconSentimentRanker:
    def analyze(self, title: str, body: str) -> SentimentResult:
        tokens = _tokenize(f"{title} {body}")
        if not tokens:
            return _build_result(score=0.0, confidence=0.15)

        positive_signal = 0.0
        negative_signal = 0.0
        for idx, token in enumerate(tokens):
            if token not in POSITIVE_WORDS and token not in NEGATIVE_WORDS:
                continue

            weight = 1.0
            prev_token = tokens[idx - 1] if idx > 0 else ""
            if prev_token in INTENSIFIERS:
                weight *= 1.35
            elif prev_token in DAMPENERS:
                weight *= 0.7

            polarity = 1.0 if token in POSITIVE_WORDS else -1.0
            if prev_token in NEGATIONS:
                polarity *= -1.0

            if polarity > 0:
                positive_signal += weight
            else:
                negative_signal += weight

        denominator = positive_signal + negative_signal
        if denominator == 0:
            return _build_result(score=0.0, confidence=0.2)

        score = (positive_signal - negative_signal) / denominator
        confidence = min(0.9, 0.25 + denominator * 0.16)
        return _build_result(score=score, confidence=confidence)


class YandexSentimentRanker:
    def __init__(self) -> None:
        self.api_key = os.getenv("YANDEX_API_KEY", "").strip()
        self.endpoint = (
            os.getenv("YANDEX_GPT_ENDPOINT")
            or "https://llm.api.cloud.yandex.net/foundationModels/v1/completion"
        ).strip()
        self.model_uri = self._resolve_model_uri()

    def _resolve_model_uri(self) -> str:
        model_uri = os.getenv("YANDEX_MODEL_URI", "").strip()
        if model_uri:
            return model_uri

        folder_id = os.getenv("YANDEX_FOLDER_ID", "").strip()
        if folder_id:
            return f"gpt://{folder_id}/yandexgpt-lite/latest"
        return ""

    def is_configured(self) -> bool:
        return bool(self.api_key and self.model_uri)

    def analyze(self, title: str, body: str) -> SentimentResult:
        if not self.is_configured():
            raise RuntimeError("Yandex sentiment ranker is not configured.")

        system_prompt = (
            "You are a senior financial news analyst. "
            "Evaluate sentiment for investors using facts from the text only. "
            "Return strict JSON only with fields: "
            '{"score": float, "confidence": float, "drivers": [str]}. '
            "Rules: score in [-1,1], confidence in [0,1], drivers length 1..3."
        )
        user_prompt = f"Title: {title}\nBody: {body}"

        payload = {
            "modelUri": self.model_uri,
            "completionOptions": {
                "stream": False,
                "temperature": 0,
                "maxTokens": "64",
            },
            "messages": [
                {"role": "system", "text": system_prompt},
                {"role": "user", "text": user_prompt},
            ],
        }
        headers = {"Authorization": f"Api-Key {self.api_key}"}

        with httpx.Client(timeout=15.0) as client:
            response = client.post(self.endpoint, headers=headers, json=payload)
            response.raise_for_status()
            response_json = response.json()

        text = (
            response_json.get("result", {})
            .get("alternatives", [{}])[0]
            .get("message", {})
            .get("text", "")
        )

        parsed = self._parse_payload(text)
        return _build_result(parsed["score"], parsed["confidence"])

    @staticmethod
    def _parse_payload(text: str) -> dict[str, float]:
        try:
            data = json.loads(text)
            score = float(data["score"])
            confidence = float(data.get("confidence", min(1.0, abs(score) + 0.2)))
            return {"score": score, "confidence": confidence}
        except (ValueError, KeyError, TypeError, json.JSONDecodeError):
            match = re.search(r"-?\d+(?:\.\d+)?", text)
            if not match:
                raise ValueError("Could not parse sentiment score from Yandex response.") from None
            score = float(match.group(0))
            return {"score": score, "confidence": min(0.85, abs(score) + 0.25)}


SentimentProvider = Literal["auto", "local", "yandex"]


class SentimentRanker:
    def __init__(self, provider: SentimentProvider = "auto") -> None:
        self.provider = provider
        self.local_ranker = LexiconSentimentRanker()
        self.yandex_ranker = YandexSentimentRanker()

    def analyze(self, title: str, body: str) -> SentimentResult:
        if self.provider == "local":
            return self.local_ranker.analyze(title, body)

        if self.provider == "yandex":
            try:
                return self.yandex_ranker.analyze(title, body)
            except (httpx.HTTPError, ValueError, RuntimeError):
                return self.local_ranker.analyze(title, body)

        if self.yandex_ranker.is_configured():
            try:
                yandex_result = self.yandex_ranker.analyze(title, body)
                local_result = self.local_ranker.analyze(title, body)
                disagreement = abs(yandex_result.score - local_result.score)

                blended_score = yandex_result.score * 0.75 + local_result.score * 0.25
                blended_confidence = (
                    yandex_result.confidence * 0.7
                    + local_result.confidence * 0.3
                    - disagreement * 0.2
                )
                return _build_result(blended_score, blended_confidence)
            except (httpx.HTTPError, ValueError):
                return self.local_ranker.analyze(title, body)

        return self.local_ranker.analyze(title, body)
