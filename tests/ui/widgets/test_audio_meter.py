import pytest
from src.ui.widgets.audio_meter import AudioMeter
import numpy as np
from textual.strip import Strip
from collections import deque
from textual.geometry import Size
from unittest.mock import Mock
from textual.app import App
from textual._context import active_app
from typing import Generator


@pytest.fixture
def audio_meter() -> AudioMeter:
    meter = AudioMeter(id="test-meter")
    # Mock the size property
    meter._size = Size(80, 10)
    return meter


@pytest.fixture
def mock_app_context() -> Generator[Mock, None, None]:
    """Create a mock app context for widgets."""
    app = Mock(spec=App)
    app._logger = Mock()
    token = active_app.set(app)
    yield app
    active_app.reset(token)


def test_audio_meter_init(audio_meter: AudioMeter) -> None:
    """Test AudioMeter initialization."""
    assert audio_meter.level == 0.0
    assert audio_meter.max_level == 0.0
    assert len(audio_meter.history) == audio_meter.history_size
    assert all(level == 0.0 for level in audio_meter.history)


def test_update_level_float32(audio_meter: AudioMeter, mock_app_context: Mock) -> None:
    """Test updating level with float32 audio data."""
    # Create sample audio data (sine wave with amplitude 1.0)
    samples = np.sin(np.linspace(0, 2 * np.pi, 1024)).astype(np.float32)
    audio_data = samples.tobytes()

    # Force update by setting last_update to old value
    audio_meter.last_update = 0
    audio_meter.update_level(audio_data, format_width=4)

    assert audio_meter.level > 0.0
    assert audio_meter._dynamic_max > 0.0


def test_update_level_int16(audio_meter: AudioMeter, mock_app_context: Mock) -> None:
    """Test updating level with int16 audio data."""
    # Create sample audio data (sine wave)
    samples = (np.sin(np.linspace(0, 2 * np.pi, 1024)) * 32767).astype(np.int16)
    audio_data = samples.tobytes()

    # Force update by setting last_update to old value
    audio_meter.last_update = 0
    audio_meter.update_level(audio_data, format_width=2)

    assert audio_meter.level > 0.0
    assert audio_meter._dynamic_max > 0.0


def test_render_line_plot(audio_meter: AudioMeter) -> None:
    """Test rendering plot lines."""
    # Set up test data
    audio_meter.level = 0.5
    audio_meter.max_level = 0.7
    audio_meter.history = deque(
        [0.5] * audio_meter.history_size, maxlen=audio_meter.history_size
    )

    # Test rendering plot lines
    for y in range(audio_meter._size.height):
        segments = audio_meter.render_line(y)
        assert isinstance(segments, Strip)


def test_level_decay(audio_meter: AudioMeter, mock_app_context: Mock) -> None:
    """Test that the level decays over time."""
    audio_meter.level = 1.0
    audio_meter._dynamic_max = 1.0

    # Create silent audio data
    samples = np.zeros(1024, dtype=np.float32)
    audio_data = samples.tobytes()

    # Force update by setting last_update to old value
    audio_meter.last_update = 0

    # Update multiple times
    for _ in range(5):
        audio_meter.update_level(audio_data, format_width=4)

    assert audio_meter.level < 1.0
    assert audio_meter._dynamic_max < 1.0
