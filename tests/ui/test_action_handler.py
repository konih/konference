from unittest.mock import Mock, AsyncMock
import pytest
from textual.widgets import Button, Label
from src.ui.action_handler import ActionHandler
from src.meeting_note import MeetingNote
import logging


@pytest.fixture
def mock_app() -> Mock:
    """Create a mock app with required attributes and methods."""
    app = Mock()
    app.logger = Mock()
    app.logger.logger = Mock()
    # Mock getEffectiveLevel to return a real logging level
    app.logger.logger.getEffectiveLevel.return_value = logging.INFO
    app.recording = False
    app.start_time = None
    app.meeting_store = Mock()
    app.meeting_store.current_meeting = None
    app.show_meeting_form = AsyncMock()

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
    return app


@pytest.fixture
def action_handler(mock_app: Mock) -> ActionHandler:
    """Create an ActionHandler instance with a mock app."""
    return ActionHandler(mock_app)


@pytest.mark.asyncio
async def test_new_meeting(mock_app: Mock, action_handler: ActionHandler) -> None:
    """Test creating a new meeting."""
    await action_handler.new_meeting()
    mock_app.show_meeting_form.assert_awaited_once()


@pytest.mark.asyncio
async def test_new_meeting_cancelled(mock_app: Mock, action_handler: ActionHandler) -> None:
    """Test cancelling new meeting creation."""
    mock_app.show_meeting_details.return_value = None
    await action_handler.new_meeting()
    mock_app.meeting_store.create_meeting.assert_not_called()


@pytest.mark.asyncio
async def test_edit_meeting(mock_app: Mock, action_handler: ActionHandler) -> None:
    """Test editing an existing meeting."""
    current_meeting = Mock()
    current_meeting.title = "Old Title"
    current_meeting.participants = ["Bob"]
    current_meeting.tags = ["old"]
    mock_app.meeting_store.current_meeting = current_meeting

    await action_handler.edit_meeting()
    mock_app.show_meeting_form.assert_awaited_once_with(
        title="Old Title", participants=["Bob"], tags=["old"]
    )


@pytest.mark.asyncio
async def test_edit_meeting_no_current_meeting(mock_app: Mock, action_handler: ActionHandler) -> None:
    """Test editing when no meeting is active."""
    mock_app.meeting_store.current_meeting = None
    await action_handler.edit_meeting()
    mock_app.show_meeting_details.assert_not_called()


@pytest.mark.asyncio
async def test_edit_meeting_cancelled(mock_app: Mock, action_handler: ActionHandler) -> None:
    """Test cancelling meeting edit."""
    current_meeting = Mock(spec=MeetingNote)
    current_meeting.title = "Old Title"
    current_meeting.participants = ["Bob"]
    current_meeting.tags = ["old"]
    mock_app.meeting_store.current_meeting = current_meeting
    mock_app.show_meeting_details.return_value = None

    await action_handler.edit_meeting()
    assert current_meeting.title == "Old Title"
    assert current_meeting.participants == ["Bob"]
    assert current_meeting.tags == ["old"]
    current_meeting.save.assert_not_called()


@pytest.mark.asyncio
async def test_start_recording(action_handler: ActionHandler, mock_app: Mock) -> None:
    """Test starting recording."""
    mock_app.meeting_store.current_meeting = Mock(title="Test Meeting")
    mock_app.start_recording = AsyncMock()
    mock_app.recording = False

    await action_handler.start_recording()
    mock_app.start_recording.assert_awaited_once_with("Test Meeting")


@pytest.mark.asyncio
async def test_start_recording_no_meeting(action_handler: ActionHandler, mock_app: Mock) -> None:
    """Test attempting to start recording without an active meeting."""
    mock_app.meeting_store.current_meeting = None
    await action_handler.start_recording()
    mock_app.notify.assert_called_once_with(
        "Please create a new meeting first", title="⚠️ Warning"
    )


def test_take_screenshot(action_handler: ActionHandler, mock_app: Mock) -> None:
    """Test screenshot action."""
    action_handler.take_screenshot()
    mock_app.notify.assert_called_once_with("Screenshot saved!", title="📸 Screenshot")


def test_open_settings(action_handler: ActionHandler, mock_app: Mock) -> None:
    """Test settings action."""
    action_handler.open_settings()
    mock_app.notify.assert_called_once_with(
        "Settings dialog coming soon!", title="⚙️ Settings"
    )


def test_summarize(action_handler: ActionHandler, mock_app: Mock) -> None:
    """Test summarize action."""
    # Test when no meeting is active
    action_handler.summarize()
    mock_app.notify.assert_called_once_with("No active meeting!", title="📝 Summary")

    # Test with active meeting
    mock_app.notify.reset_mock()
    mock_app.meeting_store.current_meeting = Mock()
    mock_app.meeting_store.current_meeting.get_summary.return_value = "Test summary"

    action_handler.summarize()
    mock_app.notify.assert_called_once_with("Test summary", title="📝 Meeting Summary")


def test_toggle_log_level(action_handler: ActionHandler, mock_app: Mock) -> None:
    """Test log level toggle."""
    # Mock the current log level
    mock_app.logger.logger.getEffectiveLevel.return_value = logging.INFO

    # Toggle log level
    action_handler.toggle_log_level()

    # Verify the log level was changed to WARNING (next in sequence)
    mock_app.logger.set_level.assert_called_with("WARNING")
