import pytest
from src.speech_transcriber import SpeechTranscriber
from src.config import Config
from unittest.mock import MagicMock, patch
import azure.cognitiveservices.speech as speechsdk


@pytest.fixture
def mock_config():
    config = MagicMock(spec=Config)
    config.get_azure_credentials.return_value = {
        "speech_key": "test_key",
        "speech_region": "test_region",
    }
    return config


@pytest.fixture
def mock_speech_recognizer():
    with patch("azure.cognitiveservices.speech.SpeechRecognizer") as mock:
        mock_instance = MagicMock()
        mock.return_value = mock_instance
        yield mock_instance


def test_speech_transcriber_init(mock_config):
    """Test SpeechTranscriber initialization."""
    transcriber = SpeechTranscriber(mock_config)
    assert transcriber.config == mock_config


def test_start_transcription(mock_config, mock_speech_recognizer):
    """Test starting transcription."""
    transcriber = SpeechTranscriber(mock_config)

    # Simulate recognition events
    def simulate_recognition(evt_handler):
        evt = MagicMock()
        evt.result.reason = speechsdk.ResultReason.RecognizedSpeech
        evt.result.text = "Test transcription"
        evt_handler(evt)

    mock_speech_recognizer.recognized.connect.side_effect = simulate_recognition

    # Get first transcription
    transcription = next(transcriber.start_transcription())
    assert transcription == "Test transcription"


def test_stop_transcription(mock_config, mock_speech_recognizer):
    """Test stopping transcription."""
    transcriber = SpeechTranscriber(mock_config)
    transcriber.stop_transcription()
    mock_speech_recognizer.stop_continuous_recognition.assert_called_once()
