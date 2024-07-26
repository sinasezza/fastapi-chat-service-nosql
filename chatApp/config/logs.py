import logging
from logging import Logger
from logging.handlers import RotatingFileHandler
from pathlib import Path

from .config import BASE_DIR, get_settings

settings = get_settings()

# Ensure the log directory exists
log_path = Path(BASE_DIR / settings.log_file_path)
try:
    log_path.parent.mkdir(parents=True, exist_ok=True)
except Exception as e:
    print(f"Error creating log directory: {e}")
    raise

# Define logging format
LOG_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"

# Configure the root logger
try:
    logging.basicConfig(
        level=settings.log_level.upper(),  # Ensure it's uppercase
        format=LOG_FORMAT,
        handlers=[
            logging.StreamHandler(),  # Log to console
            RotatingFileHandler(
                log_path,
                maxBytes=settings.log_max_bytes,
                backupCount=settings.log_backup_count,
            ),  # Log to file with rotation
        ],
    )
except Exception as e:
    print(f"Error setting up logging: {e}")
    raise

logging.getLogger("passlib").setLevel(logging.ERROR)

# Get a logger instance
logger: Logger = logging.getLogger("ChatApp")

# Example log message to test configuration
logger.info("Logging configuration is set up.")


def get_logger(name: str) -> Logger:
    return logging.getLogger(name)
