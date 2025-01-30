from textual.widget import Widget
from textual.reactive import reactive
from rich.segment import Segment
from rich.style import Style
from textual.strip import Strip
import numpy as np
from collections import deque
import time
import plotext as plt
from typing import Any


class AudioMeter(Widget):
    """A widget that displays audio input levels over time using plotext."""

    DEFAULT_CSS = """
    AudioMeter {
        height: 10;
        border: none;
        padding: 0;
        background: $surface;
    }
    """

    level: reactive[float] = reactive(0.0)
    decay_factor = 0.9

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)
        self.max_level = 0.0
        self.decay = 0.05  # Level decay rate when no signal
        self.history_size = 50  # Reduced history size
        self.history = deque([0.0] * self.history_size, maxlen=self.history_size)
        self.time_points = list(range(self.history_size))
        self.last_update = time.time()
        self.update_interval = 0.2  # Increased to 200ms
        self._last_level = 0.0
        self._sample_count = 0
        self._level_sum = 0.0
        self._last_logged_level = 0.0
        self._log_threshold = 0.05  # Only log changes greater than 5%

    def update_level(self, audio_data: bytes, format_width: int = 4) -> None:
        """Update the audio level from raw audio data."""
        try:
            current_time = time.time()
            
            # Convert bytes to numpy array based on format
            if format_width == 4:  # Float32
                samples = np.frombuffer(audio_data, dtype=np.float32)
            elif format_width == 2:  # Int16
                samples = np.frombuffer(audio_data, dtype=np.int16).astype(np.float32) / 32768.0
            else:
                return

            # Calculate RMS level
            rms = np.sqrt(np.mean(samples**2))
            level = min(1.0, rms * 4.0)

            # Accumulate levels
            self._level_sum += level
            self._sample_count += 1

            # Only update display periodically
            if current_time - self.last_update >= self.update_interval:
                # Calculate average level
                avg_level = self._level_sum / self._sample_count if self._sample_count > 0 else 0.0
                
                # Apply smoothing
                smoothing = 0.7
                self.level = smoothing * self._last_level + (1 - smoothing) * avg_level
                self.max_level = max(self.max_level * self.decay_factor, self.level)
                self._last_level = self.level

                # Only log if the level change is significant
                if abs(self.level - self._last_logged_level) > self._log_threshold:
                    self.log.debug(f"Audio level: {self.level:.3f}")
                    self._last_logged_level = self.level

                # Add to history
                self.history.append(self.level)
                
                # Reset accumulators
                self._level_sum = 0.0
                self._sample_count = 0
                self.last_update = current_time
                
                # Refresh the display
                self.refresh()

        except Exception as e:
            self.log.error(f"Error in update_level: {e}")

    def render_line(self, y: int) -> Strip:
        """Render a single line of the widget."""
        try:
            # Clear previous plot
            plt.clear_figure()
            plt.clear_data()

            # Set up the plot
            plt.plotsize(self.size.width, self.size.height)
            plt.theme("dark")
            plt.grid(False)

            # Plot the audio level history
            plt.plot(self.time_points, list(self.history))

            # Add peak line
            plt.plot(
                [0, self.history_size - 1],
                [self.max_level, self.max_level],
                color="red",
            )

            # Customize the plot
            plt.ylim(0, 1)
            plt.xlabel("")
            plt.ylabel("")
            plt.ticks_color("white")

            # Get the plot as text
            plot_text = plt.build().split("\n")

            # Return the appropriate line as a Strip
            if 0 <= y < len(plot_text):
                return Strip([Segment(plot_text[y], Style(color="white"))])
            return Strip([Segment(" " * self.size.width, Style())])
        except Exception as e:
            self.log.error(f"Error in render_line: {e}")
            return Strip([Segment(" " * self.size.width, Style())])
