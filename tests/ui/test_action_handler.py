from unittest.mock import Mock, patch
import pytest
from textual.widgets import Button, Label
from src.ui.action_handler import ActionHandler
from src.logger import AppLogger
from datetime import datetime
from typing import Any


@pytest.fixture
def mock_app() -> Mock:
    """Create a mock app with required attributes and methods."""
    app = Mock()
    app.logger = AppLogger()
    app.recording = False
    app.start_time = None

    # Mock widgets
    toggle_button = Mock(spec=Button)
    status_label = Mock(spec=Label)

    # Setup query_one to return our mock widgets
    def mock_query_one(selector: str) -> Any:
        if selector == "#toggle":
            return toggle_button
        elif selector == "#status":
            return status_label
        raise ValueError(f"Unexpected selector: {selector}")

    app.query_one = mock_query_one
    return app


@pytest.fixture
def action_handler(mock_app: Mock) -> ActionHandler:
    """Create an ActionHandler instance with a mock app."""
    return ActionHandler(mock_app)


@pytest.mark.asyncio(loop_scope="function")
async def test_toggle_recording_start(
    action_handler: ActionHandler, mock_app: Mock
) -> None:
    """Test starting recording."""
    with patch("asyncio.create_task") as mock_create_task:
        action_handler.toggle_recording()

        assert mock_app.recording is True
        toggle_btn = mock_app.query_one("#toggle")
        status = mock_app.query_one("#status")

        assert isinstance(mock_app.start_time, datetime)
        toggle_btn.label = "🛑 Stop"
        toggle_btn.classes = "action-button -recording"
        status.update.assert_called_once()

        # Check both timer and recording tasks were created
        assert mock_create_task.call_count == 2
        calls = mock_create_task.call_args_list
        assert any(call.args[0] == mock_app._start_timer() for call in calls)
        assert any(call.args[0] == mock_app.start_recording() for call in calls)


@pytest.mark.asyncio(loop_scope="function")
async def test_toggle_recording_stop(
    action_handler: ActionHandler, mock_app: Mock
) -> None:
    """Test stopping recording."""
    # Set initial state to recording
    mock_app.recording = True

    with patch("asyncio.create_task") as mock_create_task:
        action_handler.toggle_recording()

        assert mock_app.recording is False
        toggle_btn = mock_app.query_one("#toggle")
        status = mock_app.query_one("#status")

        toggle_btn.label = "🎙 Start"
        toggle_btn.classes = "action-button"
        status.update.assert_called_once_with("Ready")
        mock_app._stop_timer.assert_called_once()
        mock_create_task.assert_called_once_with(mock_app.stop_recording())


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
    action_handler.summarize()
    mock_app.notify.assert_called_once_with(
        "Meeting summary coming soon!", title="📝 Summary"
    )


def test_toggle_log_level(action_handler: ActionHandler, mock_app: Mock) -> None:
    """Test log level toggle."""
    # Set initial log level
    mock_app.logger.set_level("INFO")

    # Toggle log level
    action_handler.toggle_log_level()

    # Check if log level was changed to next level (WARNING)
    current_level = mock_app.logger.logger.getEffectiveLevel()
    assert current_level == 30  # WARNING level
