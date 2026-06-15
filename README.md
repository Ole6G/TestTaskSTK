# RU News Analysis PoC

Prototype service for analyzing `.ru` company news stream:
- clustering by `company_name + location + industry` and text similarity;
- sentiment scoring and ranking on scale `[-100, 100]`;
- FastAPI API with optional persistence in PostgreSQL.

## Stack
- Python 3.12
- FastAPI
- SQLAlchemy
- PostgreSQL (via Docker)
- Docker / docker-compose

## Layered Architecture
- `app/presentation` - FastAPI routers and request/response schemas
- `app/application` - use-cases and orchestration services
- `app/domain` - pure business logic, entities, repository ports
- `app/infrastructure` - SQLAlchemy models/session and repository adapters

Project is organized so business rules stay independent from transport and storage details.

## Run with Docker
```bash
docker compose up --build
```

API docs:
- Swagger UI: `http://localhost:8000/docs`
- Healthcheck: `http://localhost:8000/health`

## Local run (without Docker)
```bash
python -m venv .venv
# Linux/macOS: source .venv/bin/activate
# Windows PowerShell: .venv\Scripts\Activate.ps1
pip install -r requirements.txt
uvicorn app.main:app --reload
```

By default local run uses SQLite (`sqlite:///./news.db`).
Set `DATABASE_URL` for PostgreSQL explicitly when needed.

## Database Migrations (Alembic)
- Migrations are managed in `alembic/versions`.
- On API startup, app runs `alembic upgrade head` automatically.
- Alembic is the single source of truth for schema changes.

Manual commands:
```bash
alembic upgrade head
alembic downgrade -1
alembic revision -m "describe change"
```

Makefile shortcuts:
```bash
make ci
make migrate
make migrate-down
make revision msg="describe change"
```

## Main endpoints
- `POST /api/news/analyze` - analyze JSON payload:
  - computes clusters and sentiment ranking;
  - returns `sentiment_confidence` for each item;
  - persists to DB when `persist=true`.
- `POST /api/news/analyze-file` - analyze `.json` or `.csv` file upload.
- `GET /api/news/clusters` - return top clusters with average sentiment.

## Sentiment providers
You can choose sentiment mode via `sentiment_provider`:
- `auto` (default) - blend YandexGPT (75%) with local ranker (25%) for more stable output
- `local` - always use local lexicon-based ranker
- `yandex` - try YandexGPT first, fallback to local ranker on any API/config error

### YandexGPT configuration (optional)
Set env vars to enable cloud sentiment:
- `YANDEX_API_KEY`
- `YANDEX_FOLDER_ID` (or `YANDEX_MODEL_URI`)
- optional `YANDEX_GPT_ENDPOINT` (default is Yandex Foundation Models completion endpoint)

## Tests
```bash
pytest
make ci
```

## Capacity assumptions for PoC
- Target: 100 news/day.
- Sizing baseline: `2 vCPU`, `4 GB RAM`, `20 GB SSD`.
- Scale path:
  - 10k/day: add queue + workers, increase DB and CPU.
  - 100k/day: horizontal workers, partitioning, monitoring, retries/DLQ.
