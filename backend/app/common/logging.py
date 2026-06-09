import logging
import sys

from app.common.config import settings


def setup_logging() -> None:
    level = logging.DEBUG if settings.app_debug else logging.INFO

    formatter = logging.Formatter(
        "%(asctime)s [%(levelname)s] [%(request_id)s] %(name)s: %(message)s",
        datefmt="%Y-%m-%dT%H:%M:%S",
    )

    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(formatter)

    root_logger = logging.getLogger()
    root_logger.setLevel(level)
    root_logger.handlers.clear()
    root_logger.addHandler(handler)

    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)
    logging.getLogger("httpcore").setLevel(logging.WARNING)
    logging.getLogger("httpx").setLevel(logging.WARNING)


class RequestIDFilter(logging.Filter):
    """Inject request_id into log records via logging context."""

    def filter(self, record: logging.LogRecord) -> bool:
        record.request_id = getattr(record, "request_id", "-")
        return True


# Register the filter on the root handler after setup_logging is called.
# The formatter includes %(request_id)s which defaults to "-".
