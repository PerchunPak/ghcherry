import logging.config
import typing as t

LOGGING_CONFIG: dict[str, t.Any] = {
    "version": 1,
    "handlers": {
        "default": {
            "class": "logging.StreamHandler",
            "formatter": "http",
            "stream": "ext://sys.stdout",
        }
    },
    "formatters": {
        "http": {
            "format": "  %(message)s",
        }
    },
    "loggers": {
        "httpx": {
            "handlers": ["default"],
            "level": "INFO",
        },
        "httpcore": {
            "handlers": ["default"],
            "level": "INFO",
        },
    },
}


def setup_logging() -> None:
    logging.config.dictConfig(LOGGING_CONFIG)
