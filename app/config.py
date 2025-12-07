from __future__ import annotations

import os
from typing import Optional, Set


def _parse_bool(s: Optional[str], default: bool) -> bool:
    if s is None:
        return default
    return str(s).strip().lower() not in ("0", "false", "no", "n", "")


def _parse_set(s: Optional[str]) -> Set[str]:
    if not s:
        return set()
    return {x.strip() for x in s.split(",") if x.strip()}


class Settings:
    DATABASE_URL: str = os.getenv("DATABASE_URL", "sqlite:///./data/media.db")

    BACKUP_ENABLED: bool = _parse_bool(os.getenv("BACKUP_ENABLED", "true"), True)
    BACKUP_INTERVAL_DAYS: int = int(os.getenv("BACKUP_INTERVAL_DAYS", "7"))
    BACKUP_DEST_DIR: str = os.getenv("BACKUP_DEST_DIR", "./backups")
    MAX_CONSECUTIVE_FAILURES: int = int(os.getenv("BACKUP_MAX_FAILURES", "3"))
    FAIL_FAST_ON_STARTUP: bool = _parse_bool(
        os.getenv("BACKUP_FAIL_FAST_ON_STARTUP", "false"), False
    )

    BACKUP_ADMIN_TOKENS: Set[str] = _parse_set(os.getenv("BACKUP_ADMIN_TOKENS", ""))

    def sqlite_file_path(self) -> Optional[str]:
        url = self.DATABASE_URL or ""
        if not url.startswith("sqlite"):
            return None
        prefix = "sqlite:///"
        if url.startswith(prefix):
            return url[len(prefix) :]
        if url.startswith("sqlite:////"):
            return url.split("sqlite://", 1)[1]
        if url.startswith("sqlite://"):
            return url.split("://", 1)[1]
        return None


settings = Settings()
