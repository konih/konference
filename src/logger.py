import logging
from datetime import datetime
from pathlib import Path
from typing import Optional

from textual.widgets import Log


class UILogHandler(logging.Handler):
    """Custom logging handler that writes to the Textual UI Log widget."""

    def __init__(self) -> None:
        super().__init__()
        self.log_widget: Optional[Log] = None

    def set_log_widget(self, log_widget: Log) -> None:
        """Set the Log widget to write to."""
        self.log_widget = log_widget

    def emit(self, record: logging.LogRecord) -> None:
        if self.log_widget is None:
            return

        formatted_time = datetime.fromtimestamp(record.created).strftime("%H:%M:%S")

        # Simple format without any styling
        log_entry = f"{formatted_time} {record.levelname}: {record.getMessage()}\n"

        # Write to the log widget
        self.log_widget.write(log_entry)


class AppLogger:
    """Application logger that can write to both file and UI."""

    _instance: Optional["AppLogger"] = None

    def __new__(cls) -> "AppLogger":
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self) -> None:
        if not hasattr(self, "initialized"):
            self.logger = logging.getLogger("transcriber")
            self.ui_handler = UILogHandler()
            self.file_handler: Optional[logging.FileHandler] = None
            self.initialized = True

            # Set up basic configuration
            self.logger.setLevel(logging.INFO)

            # Create formatter
            formatter = logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")
            self.ui_handler.setFormatter(logging.Formatter("%(message)s"))
            self.logger.addHandler(self.ui_handler)

    def setup_file_logging(self, log_dir: str, enabled: bool = False) -> None:
        """Set up file logging if enabled."""
        if enabled:
            if self.file_handler:
                self.logger.removeHandler(self.file_handler)

            log_path = Path(log_dir)
            log_path.mkdir(parents=True, exist_ok=True)

            log_file = log_path / f"transcriber_{datetime.now():%Y%m%d_%H%M%S}.log"
            self.file_handler = logging.FileHandler(log_file)
            self.file_handler.setFormatter(
                logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")
            )
            self.logger.addHandler(self.file_handler)

    def set_level(self, level: str) -> None:
        """Set the logging level."""
        if isinstance(level, str):  # Add check for string type
            level_map = {
                "DEBUG": logging.DEBUG,
                "INFO": logging.INFO,
                "WARNING": logging.WARNING,
                "ERROR": logging.ERROR,
                "CRITICAL": logging.CRITICAL,
            }
            numeric_level = level_map.get(level.upper(), logging.INFO)
            self.logger.setLevel(numeric_level)

    def set_log_widget(self, log_widget: Log) -> None:
        """Set the UI Log widget for logging."""
        self.ui_handler.set_log_widget(log_widget)
