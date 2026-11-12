
import logging
from logging.handlers import RotatingFileHandler

import scripts.logging_config as logging_config


def test_configure_logging(monkeypatch, tmp_path):
    """Test the complete logging configuration."""

    # Simulate the project directory
    fake_file = tmp_path / "scripts" / "logging_config.py"

    monkeypatch.setattr(
        logging_config,
        "__file__",
        str(fake_file)
    )

    # Capture basicConfig arguments instead of changing global logging
    captured_config = {}

    def mock_basic_config(**kwargs):
        captured_config.update(kwargs)

    monkeypatch.setattr(
        logging,
        "basicConfig",
        mock_basic_config
    )

    # Execute the function
    logging_config.configure_logging()

    # Check log directory and file
    log_folder = tmp_path / "logs"
    log_file = log_folder / "etl_pipeline.log"

    assert log_folder.exists()
    assert log_folder.is_dir()
    assert log_file.exists()

    # Check logging configuration
    assert captured_config["level"] == logging.INFO
    assert captured_config["force"] is True

    handlers = captured_config["handlers"]

    assert len(handlers) == 2

    # Check console handler
    console_handler = handlers[0]

    assert isinstance(console_handler, logging.StreamHandler)
    assert console_handler.formatter is not None

    # Check rotating file handler
    file_handler = handlers[1]

    assert isinstance(file_handler, RotatingFileHandler)
    assert file_handler.maxBytes == 5 * 1024 * 1024
    assert file_handler.backupCount == 3
    assert file_handler.encoding == "utf-8"
    assert file_handler.formatter is not None

    # Check formatter
    expected_format = (
        "%(asctime)s - %(levelname)s - "
        "%(name)s - %(message)s"
    )

    assert console_handler.formatter._fmt == expected_format
    assert file_handler.formatter._fmt == expected_format

    # Close handlers to release file resources
    for handler in handlers:
        handler.close()
