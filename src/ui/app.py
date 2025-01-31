from textual.app import App, ComposeResult
from textual.containers import Container, Horizontal
from textual.widgets import Header, Footer, Button
from textual.binding import Binding
from datetime import datetime
import asyncio
from typing import Optional, List, Any, AsyncGenerator, Tuple
from src.logger import AppLogger
from src.config import Config
from src.ui.action_handler import ActionHandler
from src.speech_transcriber import SpeechTranscriber
from src.ui.widgets.audio_meter import AudioMeter
from src.audio_capture import AudioCapture
import pyaudio
from src.protocol_writer import ProtocolWriter
from src.meeting_store import MeetingStore
import signal
from rich.text import Text
from src.ui.widgets.meeting_form import MeetingForm, FormResult
from textual.widgets import Label as TextualLabel, Log as TextualLog


class Timer(TextualLabel):
    """Custom timer widget."""

    def update_time(self, text: str) -> None:
        """Update the timer text."""
        self.update(text)


class Status(TextualLabel):
    """Custom status widget with update method."""

    def update(self, text: str) -> None:
        """Update the status text."""
        self.update_content(text)


class TranscriberUI(App):
    """A Textual app for managing meeting transcription."""

    CSS = """
    Screen {
        align: center middle;
        layers: below above;
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
        overflow: hidden;
    }

    #transcript {
        height: 100%;
        border: heavy $accent;
        background: $surface;
        margin: 1;
        padding: 1;
        overflow-y: scroll;
        content-align: center middle;
        text-align: center;
    }

    /* Style for the transcript text */
    #transcript > * {
        text-align: center;
        margin: 1 1;
        width: 80%;
    }

    #transcript-container {
        height: 100%;  # Take full height
        margin: 1;
        layout: grid;
        grid-size: 1;
        grid-rows: 2fr 1fr;  # 2/3 for markdown, 1/3 for logs
        overflow: hidden;
    }

    #meeting-content {
        height: 100%;     # Take full height of grid cell
        border: heavy $accent;
        background: $surface;
        margin: 0 0 1 0;  # Add bottom margin instead of row-gap
        padding: 1;
        overflow-y: auto;
    }

    #log {
        height: 100%;     # Take full height of grid cell
        border: heavy $accent;
        background: $surface-darken-1;
        margin: 0;        # Remove margin to fill space
        margin-bottom: 3; # Keep margin for footer
        padding: 1;
        overflow-y: auto;
        text-style: none;
        content-align: left top;
    }

    .action_button {
        width: 100%;
        margin: 1 0;
        background: $primary;
    }

    .action_button:hover {
        background: $primary-lighten-2;
    }

    .action_button_recording {
        background: $error;
    }

    .action_button_recording:hover {
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

    #meeting-modal {
        background: $surface;
        padding: 1;
        border: heavy $accent;
        width: 60;
        height: 20;
        margin: 1;
    }

    #meeting-modal Input, #meeting-modal TextArea {
        margin: 1;
        width: 100%;
    }

    Footer {
        background: $boost;
        color: $text-muted;
        dock: bottom;
        height: 3;
    }

    MeetingForm {
        width: 100%;
        height: 100%;
        dock: top;
        margin: 1;
        padding: 1;
        border: heavy $accent;
        background: $surface;
    }
    """

    BINDINGS = [
        Binding("q", "quit", "Quit", show=True),
        Binding("s", "screenshot", "Screenshot", show=True),
        Binding("n", "new_meeting", "New Meeting", show=True),
        Binding("space", "toggle_recording", "Start/Stop", show=True),
        Binding("m", "summarize", "Summarize", show=True),
    ]

    def __init__(self, default_participant: Optional[str] = None):
        super().__init__()
        # Initialize config first
        self.config = Config()

        # Initialize core components
        self.meeting_store = MeetingStore(default_participant=default_participant)
        self.logger = AppLogger()
        self.transcriber = SpeechTranscriber(self.config)
        self.action_handler = ActionHandler(self)

        # Initialize state
        self.recording = False
        self.paused = False
        self.start_time: Optional[datetime] = None
        self._transcription_task: Optional[asyncio.Task] = None
        self._timer_task: Optional[asyncio.Task] = None
        self.audio_stream: Optional[AsyncGenerator[bytes, None]] = None
        self.protocol_writer: Optional[ProtocolWriter] = None
        self.last_minute: Optional[str] = None

        # Initialize audio capture with config
        audio_config = self.config.config.get(
            "audio",
            {
                "enabled": False,
                "format": pyaudio.paFloat32,
                "channels": 1,
                "rate": 16000,
                "chunk": 1024,
            },
        )
        self.audio_capture = AudioCapture(
            format=audio_config["format"],
            channels=audio_config["channels"],
            rate=audio_config["rate"],
            chunk=audio_config["chunk"],
            enabled=audio_config["enabled"],
            logger=self.logger.logger,
        )

    async def on_mount(self) -> None:
        """Handle app startup."""
        try:
            # Set up signal handler for Ctrl+C
            signal.signal(signal.SIGINT, self.handle_sigint)

            # Initial logging setup
            log_settings = self.config.get_logging_settings()
            self.logger.set_level(log_settings["level"])
            self.logger.setup_file_logging(
                self.config.get_path("logs"), log_settings["file_logging_enabled"]
            )

            # Set up logger with UI widget
            log_widget = self.query_one("#log")
            self.logger.set_log_widget(log_widget)

            # Set up audio meter - REMOVE this duplicate widget creation
            # meter = self.query_one("#audio-meter", AudioMeter)  # Remove this
            # Instead, just get the existing widget
            meter = self.query_one("#audio-meter", AudioMeter)
            self.audio_capture = AudioCapture(
                format=pyaudio.paFloat32,
                rate=44100,
                chunk=1024,
                level_callback=lambda data: meter.update_level(data, format_width=4),
                logger=self.logger.logger,
            )

            # Create default meeting if configured
            user_settings = self.config.get_user_settings()
            if user_settings["create_default_meeting"]:
                self.meeting_store.create_meeting(
                    title="Untitled Meeting",
                    participants=[user_settings["default_participant"]],
                )

            # Update UI to show initial meeting content
            self._update_recording_ui()

            # Render initial markdown if there's a current meeting
            if self.meeting_store.current_meeting:
                meeting_content = self.query_one("#meeting-content", TextualLog)
                from src.markdown_renderer import MarkdownRenderer

                markdown = MarkdownRenderer.render(self.meeting_store.current_meeting)
                meeting_content.clear()
                meeting_content.write(markdown)

            self.logger.logger.info("Application started")
            self.logger.logger.info(
                f"Audio capture initialized with format: {pyaudio.paFloat32}"
            )

        except Exception as e:
            self.logger.logger.error(f"Error during app initialization: {e}")
            raise

    def compose(self) -> ComposeResult:
        """Create child widgets for the app."""
        # Header section
        yield Header()
        yield AudioMeter(id="audio-meter")

        with Horizontal():
            # Sidebar with action buttons
            with Container(id="sidebar"):
                yield Button("🎙 New Meeting", id="new_meeting", classes="action_button")
                yield Button(
                    "✏️ Edit Meeting",
                    id="edit_meeting",
                    classes="action_button",
                    disabled=True,
                )
                yield Button(
                    "⏺ Start Recording",
                    id="start_recording",
                    classes="action_button",
                    disabled=True,
                )
                yield Button("📸 Screenshot", id="screenshot", classes="action_button")
                yield Button("📥 Export Meeting", id="export", classes="action_button")
                yield Button("📝 Summarize", id="summarize", classes="action_button")
                yield Button("🔍 Log Level", id="loglevel", classes="action_button")

            # Main content area
            with Container(id="content"):
                # Status bar
                with Horizontal(classes="status-bar"):
                    yield Status("Ready", id="status")
                    yield Timer("00:00:00", id="timer")

                # Meeting content area
                with Container(id="transcript-container"):
                    yield TextualLog(
                        id="meeting-content", highlight=True
                    )  # For rendered markdown
                    yield TextualLog(id="log", highlight=True)  # For debug logs

        yield Footer()

    async def _process_transcription(self) -> None:
        """Pull text from the SpeechTranscriber queue and add it to the meeting."""
        self.logger.logger.info("Starting local transcription consumer task")
        transcript_queue = self.transcriber.get_transcript_queue()

        try:
            self.logger.logger.debug("Entering transcription processing loop")
            while self.recording and not self.paused:
                try:
                    # Wait for recognized text with a timeout
                    text = await asyncio.wait_for(transcript_queue.get(), timeout=0.5)

                    text = text.strip()
                    if not text:
                        continue

                    if self.meeting_store.current_meeting:
                        try:
                            # Add to meeting store
                            self.meeting_store.add_content(text)
                            self.logger.logger.debug(f"Added to meeting store: {text}")

                            # Update log pane
                            log = self.query_one("#log", TextualLog)
                            log.write(f"[{datetime.now().strftime('%H:%M:%S')}] {text}")

                            # Update meeting content display
                            meeting_content = self.query_one(
                                "#meeting-content", TextualLog
                            )
                            from src.markdown_renderer import MarkdownRenderer

                            try:
                                markdown = MarkdownRenderer.render(
                                    self.meeting_store.current_meeting
                                )
                                meeting_content.clear()
                                meeting_content.write(markdown)
                                self.logger.logger.debug("Updated markdown display")
                            except Exception as e:
                                self.logger.logger.error(
                                    f"Error rendering markdown: {e}"
                                )

                            # Save meeting after each update
                            self.meeting_store.current_meeting.save()

                            self.logger.logger.debug(
                                f"Meeting state - Raw text length: {len(self.meeting_store.current_meeting.raw_text)}, "
                                f"Content items: {len(self.meeting_store.current_meeting.content)}"
                            )
                        except Exception as e:
                            self.logger.logger.error(
                                f"Error processing transcribed text: {e}", exc_info=True
                            )
                    else:
                        self.logger.logger.warning(
                            "Received transcription but no active meeting"
                        )

                except asyncio.TimeoutError:
                    continue
                except asyncio.CancelledError:
                    self.logger.logger.info("Transcription task cancelled")
                    raise
                except Exception as e:
                    self.logger.logger.error(
                        f"Error in transcription loop: {e}", exc_info=True
                    )

        except asyncio.CancelledError:
            self.logger.logger.info("Local transcription consumer cancelled")
        except Exception as e:
            self.logger.logger.error(
                f"Fatal error in transcription consumer: {e}", exc_info=True
            )
        finally:
            self.logger.logger.info("Local transcription consumer ended")

    async def action_toggle_recording(self) -> None:
        """Handle recording toggle action from key binding."""
        self.logger.logger.debug("Toggle recording key binding pressed")
        await self.action_handler.start_recording()

    async def show_meeting_form(
        self,
        title: str = "",
        participants: Optional[List[str]] = None,
        tags: Optional[List[str]] = None,
    ) -> None:
        """Show meeting form in place of meeting content."""
        self.logger.logger.info(f"Showing meeting form with title: {title}")

        # Get the meeting content widget and its parent
        meeting_content = self.query_one("#meeting-content", TextualLog)
        container = meeting_content.parent

        # Hide meeting content
        meeting_content.styles.display = "none"

        # Create and mount form
        form = MeetingForm(
            title=title,
            participants=participants,
            tags=tags,
        )

        # Mount the form
        container.mount(form)

        # The form will post FormResult messages that we'll handle in on_form_result

    async def on_form_result(self, message: FormResult) -> None:
        """Handle form result messages."""
        await self._handle_form_result(message.result)
        if message.result is not None:
            self.notify("Meeting updated successfully!", title="✅ Success")

    def _update_recording_ui(self) -> None:
        """Update UI based on recording state."""
        try:
            # Get UI elements
            timer = self.query_one("#timer", Timer)
            status = self.query_one("#status", Status)
            start_button = self.query_one("#start_recording", Button)
            edit_button = self.query_one("#edit_meeting", Button)

            # Update button states based on meeting existence
            has_meeting = self.meeting_store.current_meeting is not None
            edit_button.disabled = not has_meeting
            start_button.disabled = not has_meeting

            # Update recording button text and style
            if self.recording:
                if self.paused:
                    start_button.label = "⏵ Resume Recording"
                    status.update("⏸ Paused")
                else:
                    start_button.label = "⏸ Pause Recording"
                    status.update("🔴 Recording")
                start_button.classes = "action_button action_button_recording"
            else:
                start_button.label = "⏺ Start Recording"
                start_button.classes = "action_button"
                status.update("Ready")

            # Update timer display
            if not self.recording or self.paused:
                timer.update_time("00:00:00")

            # Update meeting content if available
            if self.meeting_store.current_meeting:
                meeting_content = self.query_one("#meeting-content", TextualLog)
                from src.markdown_renderer import MarkdownRenderer

                try:
                    markdown = MarkdownRenderer.render(
                        self.meeting_store.current_meeting
                    )
                    meeting_content.clear()
                    meeting_content.write(markdown)
                except Exception as e:
                    self.logger.logger.error(f"Error rendering markdown: {e}")

        except Exception as e:
            self.logger.logger.error(f"Error updating UI: {e}")

    async def _handle_form_result(
        self, result: Optional[Tuple[str, List[str], List[str]]]
    ) -> None:
        """Handle form submission result."""
        # Get widgets
        meeting_content = self.query_one("#meeting-content", TextualLog)
        form = self.query_one(MeetingForm)

        # Remove form
        if form:
            form.remove()

        # Show meeting content
        meeting_content.styles.display = "block"

        # Update meeting if result is provided
        if result:
            title, participants, tags = result

            # Create new meeting if none exists
            if not self.meeting_store.current_meeting:
                self.meeting_store.create_meeting(
                    title=title or "Untitled Meeting",
                    participants=participants,
                    tags=tags,
                )
            else:
                # Update existing meeting
                current = self.meeting_store.current_meeting
                current.title = title or current.title
                current.participants = participants
                current.tags = tags
                current.save()

        # Always update UI and render markdown
        self._update_recording_ui()  # Make sure to update UI after form result
        if self.meeting_store.current_meeting:
            from src.markdown_renderer import MarkdownRenderer

            try:
                markdown = MarkdownRenderer.render(self.meeting_store.current_meeting)
                meeting_content.clear()
                meeting_content.write(markdown)
            except Exception as e:
                self.logger.logger.error(f"Error rendering markdown: {e}")
                meeting_content.write("Error displaying meeting content")

    async def _start_audio_capture(self) -> None:
        """Start capturing audio (async)."""
        self.logger.logger.debug("Starting audio capture")
        generator = self.audio_capture.start_stream()
        self.audio_stream = generator
        asyncio.create_task(self._process_audio())

    async def _stop_audio_capture(self) -> None:
        """Stop capturing audio (async)."""
        self.logger.logger.debug("Stopping audio capture")
        if self.audio_stream is not None:
            # If your AudioCapture has a stop_stream method:
            await self.audio_capture.stop_stream()
            self.audio_stream = None

    async def start_recording(self, meeting_title: Optional[str] = None) -> None:
        """Start the recording and transcription process."""
        if self.recording:
            return
        self.recording = True
        self.paused = False

        if meeting_title:
            self.logger.logger.info(f"Starting recording for: {meeting_title}")
        else:
            meeting_title = "No Title"

        try:
            self.logger.logger.info("Starting audio processing")
            await self._start_audio_capture()

            # Start continuous speech recognition
            self.transcriber.start_transcription()

            # Create and start the transcription consumer task
            self._transcription_task = asyncio.create_task(
                self._process_transcription()
            )
            self.logger.logger.debug("Created transcription consumer task")

            # Mark our start time, start the timer UI
            self.start_time = datetime.now()
            await self._start_timer()
            self._update_recording_ui()
            self.logger.logger.info("Recording started successfully")

        except Exception as e:
            self.logger.logger.error(f"Error starting recording: {e}", exc_info=True)
            # Clean up if something went wrong
            self.recording = False
            if self._transcription_task:
                self._transcription_task.cancel()
            await self._stop_audio_capture()
            self._stop_timer()
            self._update_recording_ui()

    async def stop_recording(self) -> None:
        """Stop the current recording."""
        if not self.recording:
            return
        self.recording = False
        self.logger.logger.info("Stopping transcription")

        # Stop recognition in the transcriber
        await self.transcriber.stop_transcription()

        # Stop audio capture
        await self._stop_audio_capture()

        # Clean up our transcription consumer task
        if self._transcription_task:
            self._transcription_task.cancel()
            try:
                await self._transcription_task
            except asyncio.CancelledError:
                pass
            self._transcription_task = None

        # Stop the timer, update UI
        self._stop_timer()
        self._update_recording_ui()
        self.logger.logger.info("Recording stopped")

    async def _process_audio(self) -> None:
        """Process audio data in the background."""
        self.logger.logger.info("Starting audio processing")
        try:
            if not self.audio_stream:
                self.logger.logger.error("Audio stream not initialized")
                return

            async for audio_data in self.audio_stream:
                if not self.recording:
                    self.logger.logger.info(
                        "Recording stopped, ending audio processing"
                    )
                    break

                # Process the audio data chunk
                if self.audio_capture.level_callback:
                    self.audio_capture.level_callback(audio_data)

        except Exception as e:
            self.logger.logger.error(f"Audio processing error: {e}")
            await self.stop_recording()  # Stop recording on error
        finally:
            self.logger.logger.info("Audio processing ended")

    def handle_sigint(self, signum: int, frame: Any) -> None:
        """Handle Ctrl+C gracefully."""
        try:
            # Try to get the current event loop, create a new one only if necessary
            try:
                loop = asyncio.get_event_loop()
            except RuntimeError:
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)

            # Create a task to stop recording
            loop.create_task(self.stop_recording())

            # Exit the app
            self.exit()

        except Exception as e:
            self.logger.logger.error(f"Error handling SIGINT: {e}")
            # Make sure we exit even if there's an error
            self.exit()

    async def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle button press events."""
        button_id = event.button.id
        self.logger.logger.debug(f"Button pressed: {button_id}")

        # Handle non-modal buttons
        if button_id == "new_meeting":
            await self.action_handler.new_meeting()
        elif button_id == "edit_meeting":
            await self.action_handler.edit_meeting()
        elif button_id == "start_recording":
            await self.action_handler.start_recording()
        elif button_id == "export":
            if self.meeting_store.current_meeting:
                self.meeting_store.current_meeting.save()
                self.notify("Meeting exported successfully!", title="✅ Export")
        elif button_id == "screenshot":
            self.action_handler.take_screenshot()
        elif button_id == "summarize":
            self.action_handler.summarize()
        elif button_id == "loglevel":
            self.action_handler.toggle_log_level()

    def action_quit(self) -> None:
        """Quit the application."""
        self.logger.logger.info("Quit key binding pressed")
        self.logger.logger.info("Application shutting down")
        self.exit()

    def add_transcript(self, text: str) -> None:
        """Add transcribed text to the current meeting."""
        try:
            self.logger.logger.info(f"Speech recognized: {text}")

            if self.meeting_store.current_meeting:
                # Add to meeting store
                self.meeting_store.add_content(text)

                # Update the UI to show the new content
                meeting_content = self.query_one("#meeting-content", TextualLog)
                from src.markdown_renderer import MarkdownRenderer

                try:
                    markdown = MarkdownRenderer.render(
                        self.meeting_store.current_meeting
                    )
                    meeting_content.clear()
                    meeting_content.write(markdown)
                except Exception as e:
                    self.logger.logger.error(f"Error rendering markdown: {e}")
                    meeting_content.write("Error displaying meeting content")

                # Also log to the log pane
                log = self.query_one("#log", TextualLog)
                log.write(f"[{datetime.now().strftime('%H:%M:%S')}] {text}")

                # Save after each transcript to preserve content
                self.meeting_store.current_meeting.save()

                # Debug log the current state
                self.logger.logger.debug(
                    f"Current raw text length: {len(self.meeting_store.current_meeting.raw_text)}"
                )

        except Exception as e:
            self.logger.logger.error(f"Error adding transcript: {e}")

    async def _start_timer(self) -> None:
        """Start the recording timer."""
        self._timer_task = asyncio.create_task(self._run_timer())

    async def _run_timer(self) -> None:
        """Run the timer loop."""
        timer = self.query_one("#timer", Timer)
        while self.recording:
            if self.start_time:
                elapsed = datetime.now() - self.start_time
                timer.update_time(str(elapsed).split(".")[0])  # Remove microseconds

                # Update status with current meeting info
                if self.meeting_store.current_meeting:
                    status = self.query_one("#status", Status)
                    status_text = "🔴 Recording" if not self.paused else "⏸ Paused"
                    status.update(
                        Text(
                            f"{status_text} - {self.meeting_store.current_meeting.title}",
                            style="bold red" if not self.paused else "yellow",
                        )
                    )

            await asyncio.sleep(1)

    def _stop_timer(self) -> None:
        """Stop the recording timer."""
        if self._timer_task and not self._timer_task.done():
            self._timer_task.cancel()
        self._timer_task = None
        self.query_one("#timer", Timer).update_time("00:00:00")

    def action_summarize(self) -> None:
        """Show summary of current meeting."""
        self.logger.logger.info("Summarize key binding pressed")
        if self.meeting_store and self.meeting_store.current_meeting:
            summary = self.meeting_store.current_meeting.get_summary()
            self.notify(summary, title="📝 Meeting Summary")
        else:
            self.notify("No active meeting!", title="📝 Summary")

    async def pause_recording(self) -> None:
        """Pause the current recording."""
        if not self.recording or self.paused:
            return
        self.paused = True
        self.logger.logger.info("Pausing recording")

        # Make sure to await stop_transcription
        await self.transcriber.stop_transcription()

        if self._transcription_task:
            self._transcription_task.cancel()
            try:
                await self._transcription_task
            except asyncio.CancelledError:
                pass
            self._transcription_task = None

        await self._stop_audio_capture()
        self._stop_timer()
        self._update_recording_ui()
        self.logger.logger.info("Recording paused")

    async def resume_recording(self) -> None:
        """Resume the current recording."""
        if self.recording and self.paused:
            self.paused = False
            self.logger.logger.info("Resuming recording")

            await self._start_audio_capture()  # restarts capturing
            self.transcriber.start_transcription()
            self._transcription_task = asyncio.create_task(
                self._process_transcription()
            )

            await self._start_timer()
            self._update_recording_ui()
            self.logger.logger.info("Recording resumed")

    async def action_new_meeting(self) -> None:
        """Handle new meeting action from key binding."""
        self.logger.logger.debug("New meeting key binding pressed")
        await self.action_handler.new_meeting()
