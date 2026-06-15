from __future__ import annotations

import collections
import json
import sys
import urllib.request


def main() -> None:
    if len(sys.argv) < 2:
        raise SystemExit("Usage: python scripts/run_dataset.py <dataset_json_path>")

    dataset_path = sys.argv[1]
    with open(dataset_path, encoding="utf-8") as file:
        payload = json.load(file)

    request = urllib.request.Request(
        "http://localhost:8000/api/news/analyze",
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    with urllib.request.urlopen(request, timeout=90) as response:
        body = json.loads(response.read().decode("utf-8"))
        status = response.status

    print("status", status)
    print("total_items", body["total_items"])
    print("cluster_count", body["cluster_count"])

    labels = collections.Counter(item["sentiment_label"] for item in body["items"])
    avg_confidence = sum(item["sentiment_confidence"] for item in body["items"]) / len(
        body["items"]
    )
    print("label_distribution", dict(labels))
    print("avg_confidence", round(avg_confidence, 3))
    print("--- details ---")

    for item in body["items"]:
        company = item["company_name"][:12]
        label = item["sentiment_label"]
        score = item["sentiment_score"]
        confidence = item["sentiment_confidence"]
        title = item["title"][:60]
        print(f"{company:12} | {label:8} | score={score:+.3f} | conf={confidence:.3f} | {title}")


if __name__ == "__main__":
    main()
