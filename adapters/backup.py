# adapters/backup.py
import logging
import os
import random
import shutil
import string
import tempfile
from typing import Optional

logger = logging.getLogger(__name__)


def _safe_basename(name: str) -> str:
    """Возвращает безопасное имя файла или возбуждает ValueError при попытке traversal."""
    if not name:
        raise ValueError("empty filename")
    if ".." in name or "/" in name or "\\" in name:
        raise ValueError("invalid filename")
    return name


def _rand_suffix(n: int = 6) -> str:
    return "".join(random.choice(string.digits) for _ in range(n))


def safe_export_sqlite(src: str, dest_dir: str, filename: Optional[str] = None) -> str:
    """
    Экспортирует sqlite-файл src в dest_dir с именем <filename>.db.
    - создаёт dest_dir, если нужно
    - пишет в временный файл в dest_dir, fsync + close, затем os.replace -> атомарная замена
    - запрещает имя с traversal
    Возвращает путь до конечного файла.
    Логирует ключевые события и исключения.
    """
    logger.info(
        "backup: requested export src=%s to dest_dir=%s filename=%s", src, dest_dir, filename
    )

    if not os.path.isfile(src):
        logger.error("backup: source file not found: %s", src)
        raise ValueError("source file not found")

    os.makedirs(dest_dir, exist_ok=True)

    if filename:
        base = _safe_basename(filename)
    else:
        base = f"backup-{_rand_suffix(6)}"

    dest_final = os.path.join(dest_dir, f"{base}.db")

    tmp = None
    try:
        tf = tempfile.NamedTemporaryFile(
            prefix=f"{base}-", suffix=".db.tmp", dir=dest_dir, delete=False
        )
        tmp = tf.name
        tf.close()

        logger.debug("backup: copying %s -> tmp %s", src, tmp)

        with open(src, "rb") as fr, open(tmp, "wb") as fw:
            shutil.copyfileobj(fr, fw)
            fw.flush()
            os.fsync(fw.fileno())

        os.replace(tmp, dest_final)
        logger.info("backup: created %s", dest_final)
        return dest_final
    except Exception:
        logger.exception("backup: failed exporting %s to %s (tmp=%s)", src, dest_dir, tmp)
        try:
            if tmp and os.path.exists(tmp):
                os.remove(tmp)
        except Exception:
            logger.exception("backup: failed to cleanup tmp file %s", tmp)
        raise
