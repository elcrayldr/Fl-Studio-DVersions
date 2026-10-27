"""Registros estructurados (JSON por línea). Solo locales; sin telemetría."""
from __future__ import annotations

import json
import logging
import logging.handlers
from datetime import datetime, timezone
from pathlib import Path

from .config import logs_dir


class JsonFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        data = {
            "ts": datetime.now(timezone.utc).isoformat(timespec="seconds"),
            "level": record.levelname,
            "logger": record.name,
            "msg": record.getMessage(),
        }
        extra = getattr(record, "data", None)
        if extra:
            data["data"] = extra
        if record.exc_info:
            data["exc"] = self.formatException(record.exc_info)
        return json.dumps(data, ensure_ascii=False)


def setup_logging(directory: Path | None = None, level: int = logging.INFO) -> Path | None:
    log = logging.getLogger("cray")
    if log.handlers:
        return None
    log.setLevel(level)
    target = (directory or logs_dir())
    try:
        target.mkdir(parents=True, exist_ok=True)
        path = target / "cray_flp_analyzer.log"
        h = logging.handlers.RotatingFileHandler(path, maxBytes=1_000_000, backupCount=3, encoding="utf-8")
        h.setFormatter(JsonFormatter())
        log.addHandler(h)
        return path
    except OSError:
        log.addHandler(logging.NullHandler())
        return None
