from logging.config import fileConfig
from pathlib import Path
import sys

from alembic import context
from sqlalchemy import engine_from_config, pool

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT / "src"))

from bts_monitoring.core.config import get_settings
from bts_monitoring.database.base import Base

# Bắt buộc import toàn bộ model để đăng ký vào Base.metadata
from bts_monitoring.database.models.site import SiteModel
from bts_monitoring.database.models.camera import CameraModel
from bts_monitoring.database.models.ai_event import AIEventModel
from bts_monitoring.database.models.incident import IncidentModel
from bts_monitoring.database.models.mission_rule import MissionRuleModel

from bts_monitoring.database.models.incident import (
    IncidentModel,
)

from bts_monitoring.database.models.mission_rule import (
    MissionRuleModel,
)

config = context.config

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

settings = get_settings()

config.set_main_option(
    "sqlalchemy.url",
    settings.database_url.replace("%", "%%"),
)

target_metadata = Base.metadata


def run_migrations_offline() -> None:
    url = config.get_main_option("sqlalchemy.url")

    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        compare_type=True,
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    connectable = engine_from_config(
        config.get_section(
            config.config_ini_section,
            {},
        ),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            compare_type=True,
        )

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
