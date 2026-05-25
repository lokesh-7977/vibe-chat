"""Startup: try alembic, fall back to create_all + stamp if stale."""

import logging
import sys

from alembic.config import Config
from alembic import command
from sqlalchemy import create_engine, text

from app.core.config import get_settings
from app.db.base import Base
from app.db.models import *  # noqa: F401, F403

logger = logging.getLogger("startup")
logging.basicConfig(level=logging.INFO, stream=sys.stderr)

settings = get_settings()
engine = create_engine(settings.database_url)
alembic_cfg = Config("alembic.ini")

try:
    command.upgrade(alembic_cfg, "head")
    logger.info("Alembic upgrade succeeded")
except Exception as exc:
    msg = str(exc)
    if "Can't locate revision" in msg:
        logger.warning("Stale DB revision detected. Falling back to create_all + stamp...")
        with engine.connect() as conn:
            conn.execute(text("DROP TABLE IF EXISTS alembic_version"))
            conn.commit()
        Base.metadata.create_all(engine, checkfirst=True)
        command.stamp(alembic_cfg, "head")
        logger.info("Tables created and head stamped")
    else:
        logger.error("Alembic upgrade failed: %s", msg)
        raise
