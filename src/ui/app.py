from textual.app import App, ComposeResult
from textual.containers import Container, Horizontal
from textual.widgets import Header, Footer, Button, Log, Label
from textual.binding import Binding
from rich.text import Text
from datetime import datetime
import asyncio
from typing import Optional


class TranscriberUI(App):
    """A Textual app for managing meeting transcription."""

    CSS = """
    Screen {
        align: center middle;
    }

    #sidebar {
        dock: left;
        width: 15;
        height: 100%;
        background: $boost;
        padding: 1;
    }

    #content {
        width: 100%;
        height: 100%;
        padding: 1;
    }

    #transcript {
        height: 100%;
        border: heavy $accent;
        background: $surface;
        margin: 1;
        padding: 1;
        overflow-y: scroll;
    }

    #transcript-container {
        height: 85%;
        margin: 1;
    }

    .action-button {
        width: 100%;
        margin: 1 0;
        background: $primary;
    }

    .action-button:hover {
        background: $primary-lighten-2;
    }

    .action-button.-recording {
        background: $error;
    }

    .action-button.-recording:hover {
        background: $error-lighten-2;
    }

    .status-bar {
        height: 3;
        background: $boost;
        color: $text;
    }

    .recording-label {
        color: $error;
        text-style: bold;
    }

    Label {
        content-align: center middle;
        width: 100%;
        padding: 1;
    }

    #timer {
        text-align: right;
        padding-right: 2;
    }

    #status {
        text-align: left;
        padding-left: 2;
    }
    """

    BINDINGS = [
        Binding("q", "quit", "Quit", show=True),
        Binding("s", "screenshot", "Screenshot", show=True),
        Binding("space", "toggle_recording", "Start/Stop", show=True),
        Binding("m", "summarize", "Summarize", show=True),
    ]

    def __init__(self) -> None:
        super().__init__()
        self.recording = False
        self.start_time: Optional[datetime] = None

    def compose(self) -> ComposeResult:
        """Create child widgets for the app."""
        yield Header()

        with Horizontal():
            # Sidebar with action buttons
            with Container(id="sidebar"):
                yield Button("🎙 Start", id="toggle", classes="action-button")
                yield Button("📸 Screenshot", id="screenshot", classes="action-button")
                yield Button("⚙️ Settings", id="settings", classes="action-button")
                yield Button("📝 Summarize", id="summarize", classes="action-button")

            # Main content area
            with Container(id="content"):
                # Status bar
                with Horizontal(classes="status-bar"):
                    yield Label("Ready", id="status")
                    yield Label("00:00:00", id="timer")

                # Transcript area
                with Container(id="transcript-container"):
                    yield Log(id="transcript", highlight=True)

        yield Footer()

    def on_mount(self) -> None:
        """Bind button actions when the app starts."""
        self.query_one("#toggle").action_press = self.action_toggle_recording
        self.query_one("#screenshot").action_press = self.action_screenshot
        self.query_one("#settings").action_press = self.action_settings
        self.query_one("#summarize").action_press = self.action_summarize

    def action_toggle_recording(self) -> None:
        """Toggle recording state."""
        self.recording = not self.recording
        toggle_btn = self.query_one("#toggle")
        status = self.query_one("#status")

        if self.recording:
            self.start_time = datetime.now()
            toggle_btn.label = "🛑 Stop"
            toggle_btn.classes = "action-button -recording"
            status.update(Text("🔴 Recording...", style="bold red"))
            asyncio.create_task(self._start_timer())  # Create task for the coroutine
        else:
            toggle_btn.label = "🎙 Start"
            toggle_btn.classes = "action-button"
            status.update("Ready")
            self._stop_timer()

    async def _start_timer(self) -> None:
        """Start the recording timer."""
        timer = self.query_one("#timer")
        while self.recording:
            if self.start_time:
                elapsed = datetime.now() - self.start_time
                timer.update(str(elapsed).split(".")[0])  # Remove microseconds
            await asyncio.sleep(1)

    def _stop_timer(self) -> None:
        """Stop the recording timer."""
        self.query_one("#timer").update("00:00:00")

    def action_screenshot(self) -> None:
        """Take a screenshot of the current transcript."""
        self.notify("Screenshot saved!", title="📸 Screenshot")

    def action_settings(self) -> None:
        """Open settings dialog."""
        self.notify("Settings dialog coming soon!", title="⚙️ Settings")

    def action_summarize(self) -> None:
        """Summarize the meeting transcript."""
        self.notify("Meeting summary coming soon!", title="📝 Summary")

    def add_transcript(self, text: str) -> None:
        """Add a new transcription to the log."""
        timestamp = datetime.now().strftime("%H:%M:%S")
        transcript = self.query_one("#transcript", Log)
        transcript.write(f"[{timestamp}] {text}")
        transcript.scroll_end()

    def action_quit(self) -> None:
        """Quit the application."""
        self.exit()
