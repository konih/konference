import pytest
import asyncio
from datetime import datetime
from src.meeting_note import MeetingNote
from src.meeting_store import MeetingStore
from pathlib import Path
from typing import Any, Callable, AsyncGenerator
from unittest.mock import Mock, AsyncMock
from textual.pilot import Pilot

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
def mock_components() -> dict[str, Any]:
    """Create centralized mock components for testing."""
    mock_config = Mock()
    mock_config.get_speech_config = Mock(
        return_value={
            "subscription": "test_key",
            "region": "test_region",
        }
    )
    mock_config.get_logging_settings = Mock(
        return_value={
            "level": "INFO",
            "file_logging_enabled": False,
        }
    )
    mock_config.get_path = Mock(return_value="test_logs")

    mock_logger = Mock()
    mock_logger.logger = Mock()
    mock_logger.set_level = Mock()
    mock_logger.setup_file_logging = Mock()

    mock_queue = Mock(spec=asyncio.Queue)
    mock_queue.get = AsyncMock(side_effect=asyncio.TimeoutError)
    mock_queue.put = AsyncMock()

    mock_transcriber = Mock()
    mock_transcriber.start_transcription = Mock()
    mock_transcriber.stop_transcription = AsyncMock()
    mock_transcriber.get_transcript_queue = Mock(return_value=mock_queue)
    mock_transcriber._running = False

    mock_audio = Mock()
    mock_audio.start_stream = Mock(return_value=AsyncMock())
    mock_audio.stop_stream = AsyncMock()
    mock_audio.enabled = False

    mock_timer = Mock()
    mock_timer.update = Mock()

    mock_content = Mock()
    mock_content.write = Mock()
    mock_content.clear = Mock()
    mock_content.styles = Mock()
    mock_content.styles.display = "block"

    mock_log = Mock()
    mock_log.write = Mock()

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

    mock_store = Mock()
    mock_store.current_meeting = mock_meeting
    mock_store.create_meeting = Mock(return_value=mock_meeting)
    mock_store.add_content = Mock()

    # Add new mocks for language testing
    mock_transcriber.set_language = Mock()
    mock_transcriber.speech_config = Mock()

    # Add notify mock
    mock_notify = Mock()
    mock_notify.return_value = None  # Ensure notify returns None

    return {
        "config": mock_config,
        "logger": mock_logger,
        "transcriber": mock_transcriber,
        "audio": mock_audio,
        "timer": mock_timer,
        "content": mock_content,
        "log": mock_log,
        "meeting": mock_meeting,
        "store": mock_store,
        "queue": mock_queue,
        "notify": mock_notify,
    }
