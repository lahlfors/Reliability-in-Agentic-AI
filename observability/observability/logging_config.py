import logging
import logging.config
import os

def setup_logging(default_level=logging.INFO):
    """
    Sets up the logging configuration for the application.

    Args:
        default_level (int): The default logging level.
                             Defaults to logging.INFO.
    """
    log_level = os.getenv('LOG_LEVEL', default_level)
    if isinstance(log_level, str):
        log_level = logging.getLevelName(log_level.upper())

    config = {
        "version": 1,
        "disable_existing_loggers": False,
        "formatters": {
            "standard": {
                "format": "%(asctime)s - %(levelname)s - %(name)s - %(message)s",
                "datefmt": "%Y-%m-%d %H:%M:%S",
            },
            "detailed": {
                "format": "%(asctime)s - %(levelname)s - %(name)s - %(module)s.%(funcName)s:%(lineno)d - %(message)s",
                "datefmt": "%Y-%m-%d %H:%M:%S",
            },
        },
        "handlers": {
            "console": {
                "class": "logging.StreamHandler",
                "formatter": "standard",
                "level": log_level,
                "stream": "ext://sys.stdout",
            },
        },
        "loggers": {
            "": {  # Root logger
                "handlers": ["console"],
                "level": log_level,
                "propagate": True,
            },
            "google.adk": {
                "handlers": ["console"],
                "level": logging.WARNING,
                "propagate": False,
            },
             "r2a2": {
                "handlers": ["console"],
                "level": logging.INFO,
                "propagate": False,
            },
            "httpx": {
                "handlers": ["console"],
                "level": logging.WARNING,
                "propagate": False,
            }
        },
    }

    logging.config.dictConfig(config)
    logger = logging.getLogger(__name__)
    logger.info(f"Logging configured from observability package. Root level: {logging.getLevelName(log_level)}")

def get_logger(name):
    """Retrieves a logger instance."""
    return logging.getLogger(name)