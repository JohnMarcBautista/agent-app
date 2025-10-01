import json
import logging
import sys
from datetime import datetime

from app.config import settings


class JsonFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        payload = {
            "ts": datetime.utcnow().isoformat() + "Z",
            "level": record.levelname,
            "message": record.getMessage(),
            "logger": record.name,
        }
        # Include common tracing fields if provided via logging extra
        for key in ("tenant_id", "event_id", "job_id"):
            if key in record.__dict__:
                payload[key] = record.__dict__[key]
        return json.dumps(payload)


log = logging.getLogger("revin")
log.setLevel(getattr(logging, settings.log_level.upper(), logging.INFO))
handler = logging.StreamHandler(sys.stdout)
handler.setFormatter(JsonFormatter())
log.handlers.clear()
log.addHandler(handler)


