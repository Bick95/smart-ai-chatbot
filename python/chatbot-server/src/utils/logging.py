import logging

from src.settings import settings


def get_logger(name: str, *, debug: bool | None = None) -> logging.Logger:
    """Return a logger with a configured handler. Reuses existing logger to avoid duplicate handlers."""
    if not name:
        raise ValueError("Logger name must be non-empty")

    logger = logging.getLogger(name)
    logger.setLevel(
        logging.DEBUG
        if (debug if debug is not None else settings.DEBUG)
        else logging.INFO
    )

    if not logger.handlers:
        handler = logging.StreamHandler()
        handler.setFormatter(
            logging.Formatter("[%(asctime)s] %(levelname)s %(name)s: %(message)s")
        )
        logger.addHandler(handler)

    return logger
