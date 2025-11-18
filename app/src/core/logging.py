import json
import logging
import sys
from typing import Any, Dict

from .settings import Settings


def setup_logging(settings: Settings) -> None:
    level = logging.DEBUG if settings.DEBUG or settings.ENVIRONMENT == "development" else logging.INFO

    # Basic formatter (human readable) for development/test
    basic_format = "%(asctime)s | %(levelname)s | %(name)s | %(message)s"

    # JSON formatter for production
    class JsonFormatter(logging.Formatter):
        def format(self, record: logging.LogRecord) -> str:  # type: ignore[override]
            payload: Dict[str, Any] = {
                "ts": self.formatTime(record, datefmt="%Y-%m-%dT%H:%M:%S"),
                "level": record.levelname,
                "logger": record.name,
                "message": record.getMessage(),
            }
            if record.exc_info:
                payload["exc_info"] = self.formatException(record.exc_info)
            return json.dumps(payload, ensure_ascii=False)

    handler = logging.StreamHandler(sys.stdout)
    if settings.ENVIRONMENT == "production" and not settings.DEBUG:
        handler.setFormatter(JsonFormatter())
    else:
        handler.setFormatter(logging.Formatter(basic_format))

    root = logging.getLogger()
    root.handlers.clear()
    root.setLevel(level)
    root.addHandler(handler)
