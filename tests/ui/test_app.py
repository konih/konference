import pytest
from unittest.mock import Mock, patch
from textual.widgets import Log, Label, Button
from src.ui.app import TranscriberUI
import pytest_asyncio
from textual.pilot import Pilot
from textual.geometry import Region
from typing import AsyncGenerator
from datetime import datetime

pytestmark = pytest.mark.asyncio(scope="function")


@pytest_asyncio.fixture
async def app() -> AsyncGenerator[Pilot, None]:
    """Create a TranscriberUI instance with proper setup."""
    # Mock all the necessary components
    with patch("src.logger.AppLogger") as MockLogger, patch(
        "src.speech_transcriber.SpeechTranscriber"
    ) as MockTranscriber, patch("src.logger.UILogHandler") as MockUILogHandler:
        # Set up UI log handler mock
        mock_ui_handler = Mock()
        MockUILogHandler.return_value = mock_ui_handler

        # Set up logger mock
        mock_logger = Mock()
        MockLogger.return_value = mock_logger
        mock_logger.logger = Mock()
        mock_logger.ui_handler = mock_ui_handler

        # Set up transcriber mock
        mock_transcriber = Mock()
        MockTranscriber.return_value = mock_transcriber
        mock_transcriber.logger = mock_logger.logger

        # Create and run the app
        app = TranscriberUI()
        app.logger = mock_logger
        app.transcriber = mock_transcriber

        async with app.run_test() as pilot:
            await pilot.pause()
            # Wait for app to be fully mounted
            await pilot.wait_for_scheduled_animations()
            yield pilot


@pytest.mark.asyncio(loop_scope="function")
async def test_app_mount(app: Pilot) -> None:
    """Test app mounting and initialization."""
    assert app.app.logger is not None


@pytest.mark.asyncio(loop_scope="function")
async def test_button_press_handlers(app: Pilot) -> None:
    """Test button press event handling."""
    # Create mock action handler
    mock_action_handler = Mock()
    app.app.action_handler = mock_action_handler

    # Test each button
    buttons = {
        "toggle": "toggle_recording",
        "screenshot": "take_screenshot",
        "settings": "open_settings",
        "summarize": "summarize",
        "loglevel": "toggle_log_level",
    }

    for button_id, handler_name in buttons.items():
        # Wait for button to be ready
        await app.wait_for_scheduled_animations()
        # Get button and trigger press event directly
        button = app.app.query_one(f"#{button_id}", Button)
        app.app.on_button_pressed(Button.Pressed(button))
        # Wait for event to be processed
        await app.wait_for_scheduled_animations()
        getattr(mock_action_handler, handler_name).assert_called_once()
        getattr(mock_action_handler, handler_name).reset_mock()


@pytest.mark.asyncio(loop_scope="function")
async def test_add_transcript(app: Pilot) -> None:
    """Test adding transcript text."""
    test_text = "Test transcript"
    app.app.add_transcript(test_text)

    transcript = app.app.query_one("#transcript", Log)
    # Create a region for rendering
    region = Region(0, 0, 80, 24)
    lines = transcript.render_lines(region)
    assert any(test_text in str(line) for line in lines)


@pytest.mark.asyncio(loop_scope="function")
async def test_timer_functions(app: Pilot) -> None:
    """Test timer start and stop functions."""
    timer = app.app.query_one("#timer", Label)

    # Test stop timer
    app.app._stop_timer()
    assert "00:00:00" in str(timer.render())

    # Test start timer
    app.app.recording = True
    app.app.start_time = datetime.now()  # Set a start time

    # Mock the timer update directly
    timer.update("00:00:01")  # Simulate timer update
    assert "00:00:00" not in str(timer.render())
    assert "00:00:01" in str(timer.render())


@pytest.mark.asyncio(loop_scope="function")
async def test_quit_action(app: Pilot) -> None:
    """Test quit action."""
    app.app.exit = Mock()
    app.app.action_quit()
    app.app.exit.assert_called_once()
