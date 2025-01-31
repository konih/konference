import asyncio
import logging
from datetime import datetime
from pathlib import Path
from typing import Any, Callable, AsyncGenerator, Dict
from unittest.mock import Mock, AsyncMock, MagicMock

import pytest
from textual.pilot import Pilot
from textual.widgets import Button, Label

from src.meeting_note import MeetingNote
from src.meeting_store import MeetingStore
from src.state.app_state import TranscriptionLanguage, RecordingState, AppStateData

# Set asyncio as the default event loop for all async tests
pytest.register_assert_rewrite("pytest_asyncio")


def pytest_configure(config: pytest.Config) -> None:
    """Configure pytest-asyncio defaults."""
    config.option.asyncio_mode = "strict"
    # Set default loop scope to function
    config.option.asyncio_loop_scope = "function"


@pytest.fixture(scope="session")
def event_loop_policy() -> asyncio.AbstractEventLoopPolicy:
    """Create and set a new event loop policy for all tests."""
    return asyncio.get_event_loop_policy()


def pytest_collection_modifyitems(
    session: pytest.Session, config: pytest.Config, items: list[pytest.Item]
) -> None:
    """Add asyncio marks to async tests."""
    for item in items:
        if isinstance(item, pytest.Function) and asyncio.iscoroutinefunction(item.obj):
            item.add_marker(pytest.mark.asyncio(loop_scope="function"))


@pytest.fixture
def sample_meeting_note() -> MeetingNote:
    """Create a sample meeting note for testing."""
    return MeetingNote(
        title="Test Meeting",
        start_time=datetime(2024, 1, 1, 10, 0),
        participants=["Alice", "Bob"],
        tags=["important", "test"],
    )


@pytest.fixture
def meeting_store(tmp_path: Path) -> MeetingStore:
    """Create a temporary meeting store for testing."""
    return MeetingStore(storage_dir=str(tmp_path / "meetings"))


@pytest.fixture
def mock_app_context(mock_components: dict[str, Any]) -> Callable[[Any], None]:
    """Create a mock app context for testing."""

    def setup_app(app: Any) -> None:
        app._screen = Mock()
        app._driver = Mock()
        app._animator = AsyncMock()
        app.query_one = mock_components["query_one"]

    return setup_app


@pytest.fixture
async def mock_pilot() -> AsyncGenerator[Pilot, None]:
    """Create a mock pilot for testing."""
    mock = Mock(spec=Pilot)
    mock.app = Mock()
    mock.app.query_one = Mock()
    mock.app.mount = AsyncMock()
    yield mock


@pytest.fixture
def mock_speech_sdk() -> Mock:
    """Create mock for Azure Speech SDK."""
    mock_sdk = MagicMock()

    # Mock SpeechConfig
    mock_speech_config = MagicMock()
    mock_speech_config.speech_recognition_language = TranscriptionLanguage.ENGLISH.value
    mock_sdk.SpeechConfig = Mock(return_value=mock_speech_config)

    # Mock AudioConfig
    mock_audio_config = MagicMock()
    mock_sdk.audio = MagicMock()
    mock_sdk.audio.AudioConfig = Mock(return_value=mock_audio_config)

    # Mock SpeechRecognizer
    mock_recognizer = MagicMock()
    mock_recognizer.recognized = MagicMock()
    mock_recognizer.recognized.connect = Mock()
    mock_recognizer.start_continuous_recognition_async = Mock()
    mock_recognizer.stop_continuous_recognition_async = Mock()
    mock_sdk.SpeechRecognizer = Mock(return_value=mock_recognizer)

    # Mock ResultReason enum
    class MockResultReason:
        RecognizedSpeech = "RecognizedSpeech"
        NoMatch = "NoMatch"
        Canceled = "Canceled"

    mock_sdk.ResultReason = MockResultReason

    return mock_sdk


@pytest.fixture
def mock_transcriber(mock_speech_sdk: Mock) -> Mock:
    """Create a mock transcriber."""
    transcriber = Mock()
    transcriber.start_transcription = Mock()
    transcriber.stop_transcription = AsyncMock()
    transcriber.set_language = Mock()
    transcriber.get_transcript_queue = Mock(return_value=asyncio.Queue())
    return transcriber


@pytest.fixture
def mock_components(mock_speech_sdk: Mock, mock_transcriber: Mock) -> Dict[str, Any]:
    """Create mock components for testing."""
    components = {}

    # Create mock logger
    mock_logger = Mock()
    mock_logger.debug = Mock()
    mock_logger.info = Mock()
    mock_logger.warning = Mock()
    mock_logger.error = Mock()
    components["logger"] = mock_logger

    # Create mock state
    mock_state = Mock()
    state_data = AppStateData(
        recording_state=RecordingState.STOPPED,
        language=TranscriptionLanguage.ENGLISH,
        is_processing=False,
    )
    mock_state.get_state = AsyncMock(return_value=state_data)
    mock_state.can_toggle_language = AsyncMock(return_value=True)
    mock_state.toggle_language = AsyncMock(
        side_effect=[TranscriptionLanguage.GERMAN, TranscriptionLanguage.ENGLISH]
    )
    mock_state.update_state = AsyncMock()
    mock_state.toggle_summarizing = AsyncMock()
    mock_state.can_generate_summary = AsyncMock(return_value=True)
    components["state"] = mock_state

    # Create mock config
    mock_config = Mock()
    mock_config.get_speech_config.return_value = {
        "subscription": "mock-key",
        "region": "mock-region",
    }
    components["config"] = mock_config

    # Add speech SDK and transcriber mocks
    components["speech_sdk"] = mock_speech_sdk
    components["transcriber"] = mock_transcriber

    # Add other common mocks
    components["content"] = Mock()
    components["log"] = Mock()

    return components


@pytest.fixture
def mock_app() -> Mock:
    """Create a mock app with required attributes and methods."""
    app = Mock()

    # Mock logger
    app.logger = Mock()
    app.logger.logger = Mock()
    app.logger.logger.getEffectiveLevel.return_value = logging.INFO
    app.logger.set_level = Mock()

    # Mock state
    app.state = AsyncMock()
    app.state.can_generate_summary = AsyncMock(return_value=True)
    app.state.toggle_summarizing = AsyncMock()
    app.state.can_toggle_language = AsyncMock(return_value=True)
    app.state.toggle_language = AsyncMock(return_value=TranscriptionLanguage.GERMAN)
    app.state.get_state = AsyncMock(
        return_value=AppStateData(
            recording_state=RecordingState.STOPPED,
            language=TranscriptionLanguage.ENGLISH,
            is_processing=False,
        )
    )

    # Mock recording state
    app.recording = False
    app.start_time = None

    # Mock meeting store
    app.meeting_store = Mock()
    app.meeting_store.current_meeting = None
    app.show_meeting_form = AsyncMock()

    # Mock notify
    app.notify = Mock()

    # Mock widgets
    toggle_button = Mock(spec=Button)
    status_label = Mock(spec=Label)
    timer_label = Mock(spec=Label)
    new_meeting_btn = Mock(spec=Button)
    start_recording_btn = Mock(spec=Button)

    def mock_query_one(selector: str) -> Mock:
        widgets = {
            "#toggle": toggle_button,
            "#status": status_label,
            "#timer": timer_label,
            "#new_meeting": new_meeting_btn,
            "#start_recording": start_recording_btn,
        }
        return widgets.get(selector, Mock())

    app.query_one = mock_query_one

    # Mock start_recording
    app.start_recording = AsyncMock()

    return app
