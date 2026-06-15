# API Test Datasets

This folder contains ready-to-use datasets for manual API checks.

## Files
- `news_api_payload.json` - request body for `POST /api/news/analyze`
- `news_upload.csv` - file upload for `POST /api/news/analyze-file`

## Quick checks

### 1) JSON body endpoint
```bash
curl -X POST "http://localhost:8000/api/news/analyze" \
  -H "Content-Type: application/json" \
  -d @data/news_api_payload.json
```

### 2) File upload endpoint
```bash
curl -X POST "http://localhost:8000/api/news/analyze-file" \
  -F "file=@data/news_upload.csv" \
  -F "persist=false" \
  -F "similarity_threshold=0.7" \
  -F "sentiment_provider=auto"
```

## What to validate in response
- `total_items` equals number of items in dataset
- `cluster_count` is lower than `total_items` because some items should be grouped
- each item has `cluster_id`, `sentiment_score`, `sentiment_rank`, `sentiment_label`

## Yandex mode (optional)
Set:
- `YANDEX_API_KEY`
- `YANDEX_FOLDER_ID` (or `YANDEX_MODEL_URI`)

Then run with `sentiment_provider=yandex` (or leave `auto`).
