from typing import TYPE_CHECKING
from datetime import datetime
import asyncio
from rich.text import Text
import logging

if TYPE_CHECKING:
    from src.ui.app import TranscriberUI


class ActionHandler:
    """Centralized handler for UI actions with logging."""

    def __init__(self, app: "TranscriberUI") -> None:
        self.app = app
        self.logger = app.logger.logger

    def toggle_recording(self) -> None:
        """Handle recording toggle action."""
        self.app.recording = not self.app.recording
        toggle_btn = self.app.query_one("#toggle")
        status = self.app.query_one("#status")

        if self.app.recording:
            self.logger.info("Started recording")
            self.app.start_time = datetime.now()
            toggle_btn.label = "🛑 Stop"
            toggle_btn.classes = "action-button -recording"
            status.update(Text("🔴 Recording...", style="bold red"))
            asyncio.create_task(self.app._start_timer())
            asyncio.create_task(self.app.start_recording())
        else:
            self.logger.info("Stopped recording")
            toggle_btn.label = "🎙 Start"
            toggle_btn.classes = "action-button"
            status.update("Ready")
            self.app._stop_timer()
            asyncio.create_task(self.app.stop_recording())

    def take_screenshot(self) -> None:
        """Handle screenshot action."""
        self.logger.info("Taking screenshot")
        self.app.notify("Screenshot saved!", title="📸 Screenshot")

    def open_settings(self) -> None:
        """Handle settings action."""
        self.logger.info("Opening settings dialog")
        self.app.notify("Settings dialog coming soon!", title="⚙️ Settings")

    def summarize(self) -> None:
        """Handle summarize action."""
        self.logger.info("Generating meeting summary")
        self.app.notify("Meeting summary coming soon!", title="📝 Summary")

    def toggle_log_level(self) -> None:
        """Handle log level toggle action."""
        levels = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
        current_level = self.app.logger.logger.getEffectiveLevel()
        current_index = levels.index(logging.getLevelName(current_level))
        next_index = (current_index + 1) % len(levels)
        new_level = levels[next_index]

        self.app.logger.set_level(new_level)
        self.app.notify(f"Log level changed to {new_level}", title="🔍 Log Level")
        self.logger.info(f"Log level changed to {new_level}")
