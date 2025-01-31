import pytest
import pytest_asyncio
from textual.widgets import Button
from src.ui.app import TranscriberUI
from src.state.app_state import TranscriptionLanguage, RecordingState
from typing import AsyncGenerator, Any
from unittest.mock import Mock


@pytest_asyncio.fixture
async def app(mock_components: dict[str, Any]) -> AsyncGenerator[TranscriberUI, None]:
    """Create and mount a TranscriberUI instance."""
    # Create app with mocked components
    app = TranscriberUI()
    app.transcriber = mock_components["transcriber"]
    app.logger = mock_components["logger"]
    
    # Create mock button for language toggle
    mock_button = Mock(spec=Button)
    mock_button.label = "🌍 EN"
    mock_button.disabled = False
    
    # Mock query_one to return our mock button
    def mock_query_one(selector: str, *args: Any, **kwargs: Any) -> Mock:
        """Mock query_one method."""
        if selector == "#toggle_language":
            return mock_button
        return mock_components["log"]
    
    app.query_one = mock_query_one
    
    # Mock the notify method directly instead of trying to assign mock_components["notify"]
    notify_mock = Mock(return_value=None)
    app.notify = notify_mock
    
    async with app.run_test() as pilot:
        await pilot.pause()
        yield app


@pytest.mark.asyncio
async def test_language_button_updates(app: TranscriberUI) -> None:
    """Test language button updates correctly."""
    button = app.query_one("#toggle_language", Button)
    assert button.label == "🌍 EN"
    assert not button.disabled

    # Toggle language
    await app.state.toggle_language()
    await app._update_language_button()
    
    # Verify button updated
    assert button.label == "🌍 DE"
    app.transcriber.set_language.assert_called_with(TranscriptionLanguage.GERMAN)


@pytest.mark.asyncio
async def test_language_button_disabled_states(app: TranscriberUI) -> None:
    """Test language button is disabled appropriately."""
    button = app.query_one("#toggle_language", Button)
    
    # Should be enabled initially
    assert not button.disabled
    
    # Should be disabled during recording
    await app.state.update_state(recording_state=RecordingState.RECORDING)
    await app._update_language_button()
    assert button.disabled
    
    # Should be disabled during processing
    await app.state.update_state(
        recording_state=RecordingState.STOPPED,
        is_processing=True
    )
    await app._update_language_button()
    assert button.disabled
    
    # Should be enabled when stopped and not processing
    await app.state.update_state(
        recording_state=RecordingState.STOPPED,
        is_processing=False
    )
    await app._update_language_button()
    assert not button.disabled


@pytest.mark.asyncio
async def test_language_toggle_notification(app: TranscriberUI) -> None:
    """Test proper notifications when toggling language."""
    # Toggle language
    await app.state.toggle_language()
    await app._update_language_button()
    
    # Verify notification
    app.notify.assert_called_with(
        "Language switched to German",
        title="🌍 Language"
    )
