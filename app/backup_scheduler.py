import asyncio
import logging
from contextlib import asynccontextmanager
from typing import AsyncGenerator

from adapters.backup import safe_export_sqlite
from adapters.persistence import DATABASE_URL
from app.config import settings

logger = logging.getLogger(__name__)


def _sqlite_filepath_from_url(url: str) -> str:
    """Return filesystem path for common sqlite URL forms.

    Supported forms:
      - sqlite:///relative/or/absolute/path.db
      - sqlite:////absolute/path.db
    """
    if url.startswith("sqlite:///"):
        return url.replace("sqlite:///", "")
    if url.startswith("sqlite:////"):
        return url.split("sqlite://", 1)[1]
    if url.startswith("sqlite://"):
        return url.split("://", 1)[1]
    raise ValueError("unsupported db url for sqlite export")


async def _run_backup_once() -> str:
    if not DATABASE_URL.startswith("sqlite"):
        raise RuntimeError("safe_export_sqlite supports sqlite only in this implementation")
    src = _sqlite_filepath_from_url(DATABASE_URL)
    filename = f"backup-{int(asyncio.get_event_loop().time())}"
    out = await asyncio.to_thread(safe_export_sqlite, src, settings.BACKUP_DEST_DIR, filename)
    return out


async def _periodic_backup_loop(stop_event: asyncio.Event) -> None:
    interval = settings.BACKUP_INTERVAL_DAYS * 24 * 60 * 60
    consecutive_failures = 0

    try:
        await _run_backup_once()
        consecutive_failures = 0
    except Exception:
        consecutive_failures += 1
        logger.exception("Backup initial run failed (consecutive=%d)", consecutive_failures)
        if settings.FAIL_FAST_ON_STARTUP:
            logger.error("Fail-fast is enabled - re-raising startup backup error")
            raise

    while not stop_event.is_set():
        try:
            await asyncio.wait_for(stop_event.wait(), timeout=interval)
            if stop_event.is_set():
                break
        except asyncio.TimeoutError:
            try:
                await _run_backup_once()
            except Exception:
                consecutive_failures += 1
                logger.exception("Periodic backup failed (consecutive=%d)", consecutive_failures)
                if consecutive_failures >= settings.MAX_CONSECUTIVE_FAILURES:
                    logger.error(
                        "Backup failed %d times in a row - escalating", consecutive_failures
                    )
                    stop_event.set()
                    raise
            else:
                if consecutive_failures:
                    logger.info(
                        "Backup succeeded after %d failures - resetting counter",
                        consecutive_failures,
                    )
                consecutive_failures = 0


@asynccontextmanager
async def lifespan(app) -> AsyncGenerator[None, None]:
    stop_event = asyncio.Event()
    backup_task = None
    if settings.BACKUP_ENABLED:
        loop = asyncio.get_event_loop()
        backup_task = loop.create_task(_periodic_backup_loop(stop_event))
    try:
        yield
    finally:
        if backup_task:
            stop_event.set()
            await backup_task
