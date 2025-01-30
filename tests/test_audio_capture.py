import pytest
from src.audio_capture import AudioCapture
import pyaudio
from unittest.mock import MagicMock, patch
from typing import Generator


@pytest.fixture(scope="function")  # type: ignore[misc]
def mock_pyaudio() -> Generator[MagicMock, None, None]:
    with patch("pyaudio.PyAudio") as mock:
        mock_stream = MagicMock()
        mock_stream.read.return_value = b"test_audio_data"
        mock.return_value.open.return_value = mock_stream
        yield mock


def test_audio_capture_init() -> None:
    """Test AudioCapture initialization with default values."""
    capture = AudioCapture()
    assert capture.format == pyaudio.paFloat32
    assert capture.channels == 1
    assert capture.rate == 16000
    assert capture.chunk == 1024
    assert capture.stream is None


def test_audio_capture_custom_init() -> None:
    """Test AudioCapture initialization with custom values."""
    capture = AudioCapture(
        format=pyaudio.paInt16,
        channels=2,
        rate=44100,
        chunk=2048,
    )
    assert capture.format == pyaudio.paInt16
    assert capture.channels == 2
    assert capture.rate == 44100
    assert capture.chunk == 2048


def test_start_stream(mock_pyaudio: MagicMock) -> None:
    """Test starting the audio stream."""
    capture = AudioCapture()
    stream = capture.start_stream()
    data = next(stream)

    assert data == b"test_audio_data"
    mock_pyaudio.return_value.open.assert_called_once()


def test_stop_stream(mock_pyaudio: MagicMock) -> None:
    """Test stopping the audio stream."""
    capture = AudioCapture()
    next(capture.start_stream())  # Start the stream
    capture.stop_stream()

    mock_stream = mock_pyaudio.return_value.open.return_value
    mock_stream.stop_stream.assert_called_once()
    mock_stream.close.assert_called_once()
    mock_pyaudio.return_value.terminate.assert_called_once()
