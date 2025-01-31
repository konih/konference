import pytest
from src.speech_transcriber import SpeechTranscriber
from src.config import Config
from unittest.mock import MagicMock, patch, Mock
import asyncio
from typing import Generator


@pytest.fixture(scope="function")
def mock_config() -> MagicMock:
    """Create a mock config with speech settings."""
    config = MagicMock(spec=Config)
    config.get_speech_config = Mock(
        return_value={
            "subscription": "test_key",
            "region": "test_region",
        }
    )
    return config


@pytest.fixture
def mock_speech_sdk() -> Generator[dict[str, Mock], None, None]:
    """Create mock speech SDK components."""
    with (
        patch("azure.cognitiveservices.speech.SpeechConfig") as mock_config,
        patch("azure.cognitiveservices.speech.audio.AudioConfig") as mock_audio_config,
        patch("azure.cognitiveservices.speech.SpeechRecognizer") as mock_recognizer,
    ):
        # Set up mock returns
        mock_config.return_value = Mock()
        mock_audio_config.return_value = Mock()
        mock_recognizer.return_value = Mock()

        yield {
            "config": mock_config,
            "audio_config": mock_audio_config,
            "recognizer": mock_recognizer,
        }


@pytest.fixture
def transcriber(mock_config: MagicMock, mock_speech_sdk: dict) -> SpeechTranscriber:
    """Create a transcriber with mocked components."""
    with patch("os.getenv") as mock_getenv:
        mock_getenv.side_effect = (
            lambda key: "test_key" if key == "AZURE_SPEECH_KEY" else "test_region"
        )
        transcriber = SpeechTranscriber(mock_config)
        return transcriber


def test_speech_transcriber_init(mock_speech_sdk: dict[str, Mock]) -> None:
    """Test transcriber initialization."""
    transcriber = SpeechTranscriber()
    mock_speech_sdk["config"].assert_called_once()


@pytest.mark.asyncio
async def test_start_transcription(mock_speech_sdk: dict[str, Mock]) -> None:
    """Test starting transcription."""
    transcriber = SpeechTranscriber()
    transcriber.start_transcription()

    # Verify recognizer was started
    transcriber.speech_recognizer.start_continuous_recognition_async.assert_called_once()


@pytest.mark.asyncio
async def test_stop_transcription(mock_speech_sdk: dict[str, Mock]) -> None:
    """Test stopping transcription."""
    transcriber = SpeechTranscriber()
    transcriber._running = True
    await transcriber.stop_transcription()

    # Verify recognizer was stopped
    transcriber.speech_recognizer.stop_continuous_recognition_async.assert_called_once()


@pytest.mark.asyncio
async def test_queue_transfer(transcriber: SpeechTranscriber) -> None:
    """Test that text is properly transferred between queues."""
    transcriber.start_transcription()

    # Put a test message in the thread queue
    test_text = "Test message"
    transcriber._thread_queue.put(test_text)

    # Wait a short time for transfer
    await asyncio.sleep(0.2)

    # Check that message was transferred to async queue
    assert not transcriber._async_queue.empty()
    received_text = await transcriber._async_queue.get()
    assert received_text == test_text

    # Clean up
    await transcriber.stop_transcription()
