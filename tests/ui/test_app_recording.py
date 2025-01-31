import pytest
from src.ui.app import TranscriberUI
from unittest.mock import Mock, AsyncMock
from src.state.app_state import RecordingState
from typing import AsyncGenerator, Any
import pytest_asyncio

pytestmark = [pytest.mark.asyncio, pytest.mark.recording]


@pytest.fixture
def mock_transcriber() -> Mock:
    """Create a mock transcriber."""
    transcriber = Mock()
    transcriber.start_transcription = Mock()  # type: ignore
    transcriber.stop_transcription = AsyncMock()  # type: ignore
    transcriber.set_language = Mock()  # type: ignore
    return transcriber


@pytest_asyncio.fixture
async def app(mock_components: dict[str, Any]) -> AsyncGenerator[TranscriberUI, None]:
    """Create and mount a TranscriberUI instance."""
    # Create app with mocked components
    app = TranscriberUI()
    app.transcriber = mock_components["transcriber"]
    app.logger = mock_components["logger"]
    
    # Replace log widget to avoid NoActiveAppError
    mock_log = mock_components["log"]
    app.query_one = Mock(return_value=mock_log)
    
    async with app.run_test() as pilot:
        await pilot.pause()
        yield app


@pytest.mark.asyncio
async def test_start_recording(app: TranscriberUI) -> None:
    """Test starting recording."""
    await app.start_recording("Test Meeting")
    
    # Check state updates
    state = await app.state.get_state()
    assert state.recording_state == RecordingState.RECORDING
    assert app.recording is True
    assert app.paused is False
    assert app.transcriber.start_transcription.call_count == 1


@pytest.mark.asyncio
async def test_stop_recording(app: TranscriberUI) -> None:
    """Test stopping recording."""
    # Start recording first
    await app.start_recording("Test Meeting")
    
    # Then stop
    await app.stop_recording()
    
    # Check state updates
    state = await app.state.get_state()
    assert state.recording_state == RecordingState.STOPPED
    assert app.recording is False
    assert app.transcriber.stop_transcription.await_count == 1


@pytest.mark.asyncio
async def test_pause_resume_recording(app: TranscriberUI) -> None:
    """Test pausing and resuming recording."""
    # Start recording
    await app.start_recording("Test Meeting")
    state = await app.state.get_state()
    assert state.recording_state == RecordingState.RECORDING
    assert app.recording is True
    assert app.paused is False

    # Pause recording
    await app.pause_recording()
    state = await app.state.get_state()
    assert state.recording_state == RecordingState.PAUSED
    assert app.paused is True
    assert app.recording is True
    assert app.transcriber.stop_transcription.await_count == 1

    # Reset mock for resume test
    app.transcriber.stop_transcription.reset_mock()

    # Resume recording
    await app.resume_recording()
    state = await app.state.get_state()
    assert state.recording_state == RecordingState.RECORDING
    assert app.paused is False
    assert app.recording is True
    assert app.transcriber.start_transcription.call_count == 2


@pytest.mark.asyncio
async def test_recording_cleanup_on_error(app: TranscriberUI) -> None:
    """Test proper cleanup when recording fails."""
    # Make transcription start raise an error
    app.transcriber.start_transcription.side_effect = Exception("Test error")
    
    # Attempt to start recording
    with pytest.raises(Exception):
        await app.start_recording("Test Meeting")
    
    # Check proper cleanup occurred
    state = await app.state.get_state()
    assert state.recording_state == RecordingState.STOPPED
    assert not state.is_processing
    assert app.recording is False
    assert app._transcription_task is None


@pytest.mark.asyncio
async def test_recording_state_during_processing(app: TranscriberUI) -> None:
    """Test state handling during recording processing."""
    # Start recording
    await app.start_recording("Test Meeting")
    state = await app.state.get_state()
    assert state.is_processing is False  # Should be false after start completes
    
    # Stop recording
    await app.stop_recording()
    state = await app.state.get_state()
    assert state.is_processing is False  # Should be false after stop completes


# ... more recording-related tests ...
