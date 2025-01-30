import pytest
from src.speech_transcriber import SpeechTranscriber
from src.config import Config
from unittest.mock import MagicMock, patch
import azure.cognitiveservices.speech as speechsdk
from pytest import FixtureRequest
from typing import Any, Generator


@pytest.fixture(scope="function")  # type: ignore[misc]
def mock_config(request: FixtureRequest) -> MagicMock:
    config = MagicMock(spec=Config)
    config.get_azure_credentials.return_value = {
        "speech_key": "test_key",
        "speech_region": "test_region",
    }
    return config


@pytest.fixture(scope="function")  # type: ignore[misc]
def mock_speech_recognizer(request: FixtureRequest) -> Generator[MagicMock, None, None]:
    with patch("azure.cognitiveservices.speech.SpeechRecognizer") as mock:
        mock_instance = MagicMock()
        mock.return_value = mock_instance
        yield mock_instance


def test_speech_transcriber_init(mock_config: MagicMock) -> None:
    """Test SpeechTranscriber initialization."""
    transcriber = SpeechTranscriber(mock_config)
    assert transcriber.config == mock_config


def test_start_transcription(
    mock_config: MagicMock, mock_speech_recognizer: MagicMock
) -> None:
    """Test starting transcription."""
    transcriber = SpeechTranscriber(mock_config)

    # Simulate recognition events
    def simulate_recognition(evt_handler: Any) -> None:
        evt = MagicMock()
        evt.result.reason = speechsdk.ResultReason.RecognizedSpeech
        evt.result.text = "Test transcription"
        evt_handler(evt)

    mock_speech_recognizer.recognized.connect.side_effect = simulate_recognition

    # Get first transcription
    transcription = next(transcriber.start_transcription())
    assert transcription == "Test transcription"


def test_stop_transcription(
    mock_config: MagicMock, mock_speech_recognizer: MagicMock
) -> None:
    """Test stopping transcription."""
    transcriber = SpeechTranscriber(mock_config)
    transcriber.stop_transcription()
    mock_speech_recognizer.stop_continuous_recognition.assert_called_once()
