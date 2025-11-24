# Configure logging for the JobFinder application
import logging # standard logging module
from logging.handlers import RotatingFileHandler # for log file rotation
import os

# Get the base directory and create a logs folder
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
LOG_DIR = os.path.join(BASE_DIR, "logs")
os.makedirs(LOG_DIR, exist_ok=True)

def setup_logger(name, log_file, level=logging.INFO, max_bytes=5_000_000, backup_count=3):
    """
    Create and configure a logger with both file and console output.
    Files are rotated when they reach max_bytes, keeping up to backup_count files.
    """
    logger = logging.getLogger(name)
    logger.setLevel(level)
    logger.propagate = False

    # Set up file handler with rotation
    file_handler = RotatingFileHandler(
        os.path.join(LOG_DIR, log_file),
        maxBytes=max_bytes,
        backupCount=backup_count
    )
    file_formatter = logging.Formatter(
        "[%(asctime)s] %(levelname)s %(name)s: %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S"
    )
    file_handler.setFormatter(file_formatter)
    logger.addHandler(file_handler)

    # Set up console handler for terminal output
    console_handler = logging.StreamHandler()
    console_formatter = logging.Formatter("%(levelname)s %(name)s: %(message)s")
    console_handler.setFormatter(console_formatter)
    logger.addHandler(console_handler)

    return logger
