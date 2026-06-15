from __future__ import annotations

from pathlib import Path

from alembic import command
from alembic.config import Config
from app.infrastructure.persistence.session import DATABASE_URL


def run_migrations() -> None:
    project_root = Path(__file__).resolve().parents[3]
    alembic_ini = project_root / "alembic.ini"
    script_location = project_root / "alembic"

    config = Config(str(alembic_ini))
    config.set_main_option("script_location", str(script_location))
    config.set_main_option("sqlalchemy.url", DATABASE_URL)
    command.upgrade(config, "head")
