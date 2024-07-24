import logging
from logging import Logger
from logging.handlers import RotatingFileHandler
from pathlib import Path

from .config import BASE_DIR, get_settings

settings = get_settings()


# Ensure the log directory exists
log_path = Path(BASE_DIR / settings.log_file_path)
log_path.parent.mkdir(parents=True, exist_ok=True)

# Define logging format
LOG_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"

# Configure the root logger
logging.basicConfig(
    level=settings.log_level,  # Set the logging level from env
    format=LOG_FORMAT,
    handlers=[
        logging.StreamHandler(),  # Log to console
        RotatingFileHandler(
            Path(BASE_DIR / settings.log_file_path),
            maxBytes=settings.log_max_bytes,
            backupCount=settings.log_backup_count,
        ),  # Log to file with rotation
    ],
)

# Get a logger instance
logger: Logger = logging.getLogger(__name__)

# Example log message to test configuration
logger.info("Logging configuration is set up.")
