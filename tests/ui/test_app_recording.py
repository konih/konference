import pytest
from src.ui.app import TranscriberUI
from unittest.mock import Mock, AsyncMock

pytestmark = [pytest.mark.asyncio, pytest.mark.recording]


@pytest.fixture
def mock_transcriber() -> Mock:
    """Create a mock transcriber."""
    transcriber = Mock()
    transcriber.start_transcription = Mock()
    transcriber.stop_transcription = AsyncMock()
    return transcriber


@pytest.mark.asyncio
async def test_start_recording(app: TranscriberUI, mock_transcriber: Mock) -> None:
    """Test starting recording."""
    app.transcriber = mock_transcriber
    await app.start_recording("Test Meeting")
    
    assert app.recording is True
    assert app.paused is False
    assert mock_transcriber.start_transcription.call_count == 1


@pytest.mark.asyncio
async def test_stop_recording(app: TranscriberUI, mock_transcriber: Mock) -> None:
    """Test stopping recording."""
    app.transcriber = mock_transcriber
    await app.start_recording("Test Meeting")
    await app.stop_recording()
    
    assert app.recording is False
    assert mock_transcriber.stop_transcription.await_count == 1


@pytest.mark.asyncio
async def test_pause_resume_recording(app: TranscriberUI, mock_transcriber: Mock) -> None:
    """Test pausing and resuming recording."""
    app.transcriber = mock_transcriber
    await app.start_recording("Test Meeting")
    assert app.recording is True
    assert app.paused is False

    await app.pause_recording()
    assert app.paused is True
    assert app.recording is True
    assert mock_transcriber.stop_transcription.await_count == 1

    mock_transcriber.stop_transcription.reset_mock()

    await app.resume_recording()
    assert app.paused is False
    assert app.recording is True
    assert mock_transcriber.start_transcription.call_count == 2


# ... more recording-related tests ...
