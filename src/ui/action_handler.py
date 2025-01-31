import logging
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from src.ui.app import TranscriberUI


class ActionHandler:
    """Centralized handler for UI actions with logging."""

    def __init__(self, app: "TranscriberUI") -> None:
        self.app = app
        self.logger: logging.Logger = app.logger.logger

    async def new_meeting(self) -> None:
        """Create a new meeting."""
        await self.app.show_meeting_form()
        self.logger.info("Opening new meeting form")

    async def edit_meeting(self) -> None:
        """Edit the current meeting."""
        if not self.app.meeting_store.current_meeting:
            self.app.notify("No meeting to edit!", title="⚠️ Warning")
            return

        current = self.app.meeting_store.current_meeting
        self.logger.info(f"Editing meeting: {current.title}")

        await self.app.show_meeting_form(
            title=current.title, participants=current.participants, tags=current.tags
        )

    async def start_recording(self) -> None:
        """Start or pause recording."""
        if not self.app.meeting_store.current_meeting:
            self.logger.warning("Cannot start recording without an active meeting")
            self.app.notify("Please create a new meeting first", title="⚠️ Warning")
            return

        if not self.app.recording:
            # Start recording
            await self.app.start_recording(self.app.meeting_store.current_meeting.title)
        else:
            if self.app.paused:
                await self.app.resume_recording()
            else:
                await self.app.pause_recording()

    def take_screenshot(self) -> None:
        """Handle screenshot action."""
        self.logger.info("Taking screenshot")
        self.app.notify("Screenshot saved!", title="📸 Screenshot")

    def open_settings(self) -> None:
        """Handle settings action."""
        self.logger.info("Opening settings dialog")
        self.app.notify("Settings dialog coming soon!", title="⚙️ Settings")

    async def summarize(self) -> None:
        """Handle summarize action."""
        if not self.app.meeting_store.current_meeting:
            self.app.notify("No active meeting to summarize!", title="⚠️ Warning")
            return

        # Check if we can generate summary
        if not await self.app.state.can_generate_summary():
            self.app.notify(
                "Cannot generate summary while recording or processing",
                title="⚠️ Warning",
            )
            return

        try:
            await self.app.state.toggle_summarizing(True)
            self.logger.info("Generating meeting summary")

            meeting = self.app.meeting_store.current_meeting
            meeting_data = {
                "title": meeting.title,
                "date": meeting.start_time.strftime("%Y-%m-%d"),
                "duration": str(meeting.duration) if meeting.duration else "Unknown",
                "participants": ", ".join(meeting.participants),
                "content": meeting.raw_text,
            }

            self.logger.debug(f"Meeting data: {meeting_data}")

            summary = await self.app.openai_service.generate_summary(meeting_data)
            if summary:
                meeting.summary = summary
                meeting.save()
                self.app.notify("Summary generated successfully!", title="📝 Summary")
            else:
                self.app.notify("Failed to generate summary", title="❌ Error")

        except Exception as e:
            self.logger.error(f"Error generating summary: {e}")
            self.app.notify("Failed to generate summary", title="❌ Error")
        finally:
            await self.app.state.toggle_summarizing(False)

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

    def _update_recording_ui(self, recording: bool) -> None:
        """Update UI elements for recording state."""
        self.app._update_recording_ui()

    async def action_quit(self) -> None:
        """Quit the application."""
        self.logger.info("Quit key binding pressed")
        self.logger.info("Application shutting down")
        await self.app.stop_recording()
        self.app.exit()
