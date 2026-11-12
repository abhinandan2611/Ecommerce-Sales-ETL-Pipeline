
"""Central logging configuration for the ETL pipeline."""

import logging
from logging.handlers import RotatingFileHandler
from pathlib import Path


def configure_logging() -> None:
    """Configure console and rotating file logging."""

    project_root = Path(__file__).resolve().parent.parent
    log_folder = project_root / "logs"

    log_folder.mkdir(parents=True, exist_ok=True)

    log_file = log_folder / "etl_pipeline.log"

    log_format = (
        "%(asctime)s - %(levelname)s - "
        "%(name)s - %(message)s"
    )

    formatter = logging.Formatter(log_format)

    # Display logs in the terminal.
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)

    # Save logs to a file, with automatic rotation.
    file_handler = RotatingFileHandler(
        log_file,
        maxBytes=5 * 1024 * 1024,
        backupCount=3,
        encoding="utf-8"
    )
    file_handler.setFormatter(formatter)

    logging.basicConfig(
        level=logging.INFO,
        handlers=[console_handler, file_handler],
        force=True
    )
