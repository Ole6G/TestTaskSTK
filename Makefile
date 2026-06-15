.PHONY: help install run test lint format-check format ci migrate migrate-down revision

help:
	@echo "Available commands:"
	@echo "  make install        - install dependencies"
	@echo "  make run            - run API locally"
	@echo "  make test           - run test suite"
	@echo "  make lint           - run Ruff linter"
	@echo "  make format-check   - verify code formatting"
	@echo "  make format         - apply code formatting"
	@echo "  make ci             - run local CI pipeline (format-check + lint + tests)"
	@echo "  make migrate        - apply Alembic migrations to head"
	@echo "  make migrate-down   - rollback one Alembic revision"
	@echo "  make revision msg='add column' - create new Alembic revision"

install:
	python -m pip install --upgrade pip
	pip install -r requirements.txt

run:
	uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload

test:
	python -m pytest

lint:
	python -m ruff check .

format-check:
	python -m ruff format --check .

format:
	python -m ruff format .

ci: format-check lint test

migrate:
	alembic upgrade head

migrate-down:
	alembic downgrade -1

revision:
	alembic revision -m "$(msg)"
