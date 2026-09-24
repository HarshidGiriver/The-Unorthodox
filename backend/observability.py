"""Minimal JSON logging without credentials, borrower payloads or message bodies."""

import json
import logging
from datetime import datetime, timezone


class JsonFormatter(logging.Formatter):
    def format(self, record):
        output = {"time": datetime.now(timezone.utc).isoformat(), "level": record.levelname,
                  "logger": record.name, "event": record.getMessage()}
        for key in ("outbox_id", "delivery_status", "error_type"):
            if hasattr(record, key):
                output[key] = getattr(record, key)
        return json.dumps(output)


def configure_logging():
    handler = logging.StreamHandler()
    handler.setFormatter(JsonFormatter())
    logging.getLogger("backend").handlers = [handler]
    logging.getLogger("backend").setLevel(logging.INFO)
