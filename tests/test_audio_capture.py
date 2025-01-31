from typing import Any, AsyncGenerator
from typing import Generator
from unittest.mock import MagicMock, patch

import pyaudio
import pytest

from src.audio_capture import AudioCapture


@pytest.fixture(scope="function")
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


async def anext_compat(agen: AsyncGenerator[Any, Any]) -> Any:
    """Compatibility function for Python < 3.10."""
    try:
        return await agen.__anext__()
    except StopAsyncIteration:
        raise StopAsyncIteration("No more items")


@pytest.mark.asyncio
async def test_start_stream(mock_pyaudio: MagicMock) -> None:
    """Test starting the audio stream."""
    capture = AudioCapture(enabled=True)
    # Mock the stream read to return valid data size
    mock_stream = mock_pyaudio.return_value.open.return_value
    mock_stream.read.return_value = b"\x00" * (
        capture.chunk * 4
    )  # 4 bytes per float32 sample

    # Get the generator and first chunk
    stream = capture.start_stream()
    data = await anext(stream)  # Use anext instead of awaiting the generator

    assert len(data) == capture.chunk * 4


@pytest.mark.asyncio
async def test_stop_stream(mock_pyaudio: MagicMock) -> None:
    """Test stopping the audio stream."""
    capture = AudioCapture(enabled=True)
    # Mock the stream read to return valid data size
    mock_stream = mock_pyaudio.return_value.open.return_value
    mock_stream.read.return_value = b"\x00" * (
        capture.chunk * 4
    )  # 4 bytes per float32 sample

    # Get the generator and first chunk
    stream = capture.start_stream()
    await anext(stream)  # Use anext instead of awaiting the generator

    await capture.stop_stream()
    assert capture.stream is None


@pytest.mark.asyncio
async def test_audio_capture_disabled() -> None:
    """Test that disabled audio capture yields silent data."""
    capture = AudioCapture(enabled=False)

    # Get the generator
    stream = capture.start_stream()

    # Get first chunk
    chunk = await anext(stream)

    # Should be silent data
    assert chunk == b"\x00" * capture.chunk

    # Clean up
    await capture.stop_stream()


@pytest.mark.asyncio
async def test_audio_capture_enabled() -> None:
    """Test that enabled audio capture yields actual data."""
    capture = AudioCapture(enabled=True)

    # Get the generator
    stream = capture.start_stream()

    # Get first chunk
    chunk = await anext(stream)

    # Should be actual data (not all zeros)
    assert chunk != b"\x00" * capture.chunk

    # Clean up
    await capture.stop_stream()
