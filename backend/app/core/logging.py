import json
import logging
import time
from typing import Any


class JsonFormatter(logging.Formatter):
    converter = time.gmtime

    def format(self, record: logging.LogRecord) -> str:
        payload: dict[str, Any] = {
            "timestamp": self.formatTime(record, "%Y-%m-%dT%H:%M:%SZ"),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }
        payload.update(getattr(record, "structured_data", {}))
        return json.dumps(payload, default=str)


def configure_logging(level: str) -> None:
    root_logger = logging.getLogger()
    root_logger.setLevel(level.upper())
    if not root_logger.handlers:
        handler = logging.StreamHandler()
        root_logger.addHandler(handler)
    for handler in root_logger.handlers:
        handler.setFormatter(JsonFormatter())