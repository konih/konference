from textual.app import App, ComposeResult
from textual.containers import Container, Horizontal
from textual.widgets import Header, Footer, Button, Log, Label
from textual.binding import Binding
from datetime import datetime
import asyncio
from typing import Optional
from src.logger import AppLogger
from src.config import Config
from src.ui.action_handler import ActionHandler
from src.speech_transcriber import SpeechTranscriber
from src.ui.widgets.audio_meter import AudioMeter
from src.audio_capture import AudioCapture
import pyaudio


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
        height: 80%;
        margin: 1;
        layout: grid;
        grid-size: 1 2;  # One column, two rows
        grid-rows: 2fr 1fr;  # Transcript takes 2/3, log takes 1/3
    }

    #log {
        height: 100%;
        border: heavy $accent;
        background: $surface-darken-1;
        margin: 1;
        padding: 1;
        overflow-y: scroll;
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

    #audio-meter {
        dock: top;
        height: 10;
        width: 100%;
        margin: 0;
        background: $surface-darken-1;
        border-bottom: solid $primary;
        padding: 0 1;
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
        self.logger = AppLogger()
        self.action_handler = ActionHandler(self)
        self.transcriber = SpeechTranscriber()
        self._transcription_task: Optional[asyncio.Task] = None
        self.audio_capture = AudioCapture()

    def compose(self) -> ComposeResult:
        """Create child widgets for the app."""
        yield Header()
        yield AudioMeter(id="audio-meter")

        with Horizontal():
            # Sidebar with action buttons
            with Container(id="sidebar"):
                yield Button("🎙 Start", id="toggle", classes="action-button")
                yield Button("📸 Screenshot", id="screenshot", classes="action-button")
                yield Button("⚙️ Settings", id="settings", classes="action-button")
                yield Button("📝 Summarize", id="summarize", classes="action-button")
                yield Button("🔍 Log Level", id="loglevel", classes="action-button")

            # Main content area
            with Container(id="content"):
                # Status bar
                with Horizontal(classes="status-bar"):
                    yield Label("Ready", id="status")
                    yield Label("00:00:00", id="timer")

                # Transcript area
                with Container(id="transcript-container"):
                    yield Log(id="transcript", highlight=True)
                    yield Log(id="log", highlight=True)  # Add a separate log widget

        yield Footer()

    async def _process_transcription(self) -> None:
        """Process transcription in the background."""
        try:
            async for text in self.transcriber.start_transcription():
                self.add_transcript(text)
        except Exception as e:
            self.logger.logger.error(f"Transcription error: {e}")
            self.action_handler.toggle_recording()  # Stop recording on error

    def action_toggle_recording(self) -> None:
        """Toggle recording state."""
        self.action_handler.toggle_recording()

    async def start_recording(self) -> None:
        """Start the recording and transcription process."""
        if not self._transcription_task:
            # Start audio capture
            self.audio_stream = self.audio_capture.start_stream()
            # Start processing audio in background
            asyncio.create_task(self._process_audio())
            
            self._transcription_task = asyncio.create_task(
                self._process_transcription()
            )
            self.logger.logger.info("Started transcription and audio capture")

    async def stop_recording(self) -> None:
        """Stop the recording and transcription process."""
        if self._transcription_task:
            self.transcriber.stop_transcription()
            self.audio_capture.stop_stream()
            self._transcription_task.cancel()
            try:
                await self._transcription_task
            except asyncio.CancelledError:
                pass
            self._transcription_task = None
            self.logger.logger.info("Stopped transcription and audio capture")

    async def _process_audio(self) -> None:
        """Process audio data in the background."""
        try:
            async for audio_data in self.audio_stream:
                if not self.recording:
                    break
                # Process the audio data chunk
                if self.audio_capture.level_callback:
                    self.audio_capture.level_callback(audio_data)
        except Exception as e:
            self.logger.logger.error(f"Audio processing error: {e}")
            self.action_handler.toggle_recording()  # Stop recording on error

    def on_mount(self) -> None:
        """Set up the application when mounted."""
        # Initial logging setup
        config = Config()
        log_settings = config.get_logging_settings()
        self.logger.set_level(log_settings["level"])
        self.logger.setup_file_logging(
            config.get_path("logs"), log_settings["file_logging_enabled"]
        )

        # Set up logger with UI widget AFTER the widget is mounted
        log_widget = self.query_one("#log")
        self.logger.set_log_widget(log_widget)

        # Set up audio meter callback with correct format
        meter = self.query_one("#audio-meter", AudioMeter)
        self.audio_capture = AudioCapture(
            format=pyaudio.paFloat32,
            rate=44100,
            chunk=1024,
            level_callback=lambda data: meter.update_level(data, format_width=4),
            logger=self.logger.logger
        )

        # Now that everything is set up, we can start logging
        self.logger.logger.info("Application started")
        self.logger.logger.info(f"Audio capture initialized with format: {pyaudio.paFloat32}")

    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle button press events."""
        button_id = event.button.id
        if button_id == "toggle":
            self.action_handler.toggle_recording()
        elif button_id == "screenshot":
            self.action_handler.take_screenshot()
        elif button_id == "settings":
            self.action_handler.open_settings()
        elif button_id == "summarize":
            self.action_handler.summarize()
        elif button_id == "loglevel":
            self.action_handler.toggle_log_level()

    def action_quit(self) -> None:
        """Quit the application."""
        self.logger.logger.info("Application shutting down")
        self.exit()

    def add_transcript(self, text: str) -> None:
        """Add a new transcription to the log."""
        timestamp = datetime.now().strftime("%H:%M:%S")
        transcript = self.query_one("#transcript", Log)
        transcript.write(f"[{timestamp}] {text}")
        transcript.scroll_end()
        self.logger.logger.debug(f"New transcript: {text}")

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
