import asyncio
from datetime import datetime
from typing import Any, Optional, AsyncGenerator
from unittest.mock import Mock, AsyncMock, patch

import pytest_asyncio
from textual._context import active_app
from textual.widgets import Button

from src.logger import AppLogger
from src.ui.app import TranscriberUI


@pytest_asyncio.fixture
async def mock_components() -> dict:
    """Create centralized mock components for testing."""
    return {
        "config": create_mock_config(),
        "logger": create_mock_logger(),
        "transcriber": create_mock_transcriber(),
        "audio": create_mock_audio(),
        "timer": create_mock_timer(),
        "content": create_mock_content(),
        "log": create_mock_log(),
        "meeting": create_mock_meeting(),
        "store": create_mock_store(),
        "queue": create_mock_queue(),
        "state": create_mock_state(),
        "speech_sdk": create_mock_speech_sdk(),
    }


def create_mock_config() -> Mock:
    """Create a mock config component."""
    mock_config = Mock()
    mock_config.get_logging_settings.return_value = {
        "level": "INFO",
        "file_logging_enabled": False,
    }
    mock_config.get_path.return_value = "test_logs"
    mock_config.get_user_settings.return_value = {
        "default_participant": "Test User",
        "create_default_meeting": False,
    }
    # Add speech config settings
    mock_config.get_speech_config.return_value = {
        "subscription": "test-key",
        "region": "test-region",
    }
    return mock_config


def create_mock_logger() -> Mock:
    """Create a mock logger component."""
    mock_logger = Mock(spec=AppLogger)
    mock_logger.logger = Mock()
    mock_logger.set_level = Mock()
    mock_logger.setup_file_logging = Mock()
    return mock_logger


def create_mock_transcriber() -> Mock:
    """Create a mock transcriber component."""
    mock_queue = create_mock_queue()
    mock_transcriber = Mock()
    mock_transcriber.start_transcription = Mock()
    mock_transcriber.stop_transcription = AsyncMock()
    mock_transcriber.get_transcript_queue = Mock(return_value=mock_queue)
    mock_transcriber._running = False
    return mock_transcriber


def create_mock_audio() -> Mock:
    """Create a mock audio capture component."""
    mock_audio = Mock()
    mock_audio.start_stream = Mock(return_value=AsyncMock())
    mock_audio.stop_stream = AsyncMock()
    mock_audio.enabled = False
    return mock_audio


def create_mock_timer() -> Mock:
    """Create a mock timer widget."""
    mock_timer = Mock()
    mock_timer.update = Mock()
    return mock_timer


def create_mock_content() -> Mock:
    """Create a mock content widget."""
    mock_content = Mock()
    mock_content.write = Mock()
    mock_content.clear = Mock()
    mock_content.styles = Mock()
    mock_content.styles.display = "block"
    return mock_content


def create_mock_log() -> Mock:
    """Create a mock log widget."""
    mock_log = Mock()
    mock_log.write = Mock()
    return mock_log


def create_mock_meeting() -> Mock:
    """Create a mock meeting object."""
    mock_meeting = Mock()
    mock_meeting.title = "Test Meeting"
    mock_meeting.participants = []
    mock_meeting.tags = []
    mock_meeting.start_time = datetime.now()
    mock_meeting.save = Mock()
    mock_meeting.raw_text = ""
    mock_meeting.content = []
    mock_meeting.duration = None
    mock_meeting.summary = ""
    mock_meeting.metadata = {}
    return mock_meeting


def create_mock_store() -> Mock:
    """Create a mock meeting store."""
    mock_meeting = create_mock_meeting()
    mock_store = Mock()
    mock_store.current_meeting = mock_meeting
    mock_store.create_meeting = Mock(return_value=mock_meeting)
    mock_store.add_content = Mock()
    return mock_store


def create_mock_queue() -> Mock:
    """Create a mock queue."""
    mock_queue = Mock(spec=asyncio.Queue)
    mock_queue.get = AsyncMock(side_effect=asyncio.TimeoutError)
    mock_queue.put = AsyncMock()
    return mock_queue


def create_mock_state() -> Mock:
    """Create a mock app state component."""
    mock_state = Mock()
    # Make toggle_language return a coroutine
    mock_state.toggle_language = AsyncMock()
    mock_state.can_toggle_language = AsyncMock(return_value=True)
    return mock_state


def create_mock_speech_sdk() -> Mock:
    """Create a mock speech SDK component."""
    mock_sdk = Mock()
    mock_sdk.speech_config = Mock()
    mock_sdk.audio_config = Mock()
    mock_sdk.speech_recognizer = Mock()
    mock_sdk._running = False
    mock_sdk.get_transcript_queue = Mock(return_value=create_mock_queue())
    mock_sdk.start_transcription = Mock()
    mock_sdk.stop_transcription = AsyncMock()
    mock_sdk.set_language = Mock()
    return mock_sdk


@pytest_asyncio.fixture
async def app(mock_components: dict[str, Any]) -> AsyncGenerator[TranscriberUI, None]:
    """Create a test app instance with mocked components."""
    with patch("src.ui.app.SpeechTranscriber") as mock_transcriber_class:
        # Configure the mock transcriber instance
        mock_transcriber_instance = Mock()
        mock_transcriber_instance.start_transcription = Mock()
        mock_transcriber_instance.stop_transcription = AsyncMock()
        mock_transcriber_instance.get_transcript_queue = Mock(
            return_value=mock_components["queue"]
        )
        mock_transcriber_instance._running = False

        # Make the mock class return our configured instance
        mock_transcriber_class.return_value = mock_transcriber_instance

        app = TranscriberUI(default_participant="Test User")
        active_app.set(app)

        # Set up basic app requirements
        app._screen = Mock()
        app._driver = Mock()

        # Set up components
        app.config = mock_components["config"]
        app.logger = mock_components["logger"]
        app.audio_capture = mock_components["audio"]
        app.meeting_store = mock_components["store"]
        app.state = mock_components["state"]
        app.speech_transcriber = mock_components["speech_sdk"]

        def mock_query_one(selector: str, widget_type: Optional[type] = None) -> Any:
            if selector == "#timer":
                return mock_components["timer"]
            elif selector == "#meeting-content":
                return mock_components["content"]
            elif selector == "#log":
                return mock_components["log"]
            elif selector == "#status":
                return Mock()
            elif selector == "#language_toggle":
                toggle = Mock(spec=Button)
                toggle.disabled = False
                toggle.label = Mock()
                return toggle
            return Mock()

        app.query_one = mock_query_one  # type: ignore[method-assign]
        app.action_toggle_language = AsyncMock()

        async with app.run_test():
            yield app

        active_app.set(None)
