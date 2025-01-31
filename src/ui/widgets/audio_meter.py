from textual.widget import Widget
from textual.reactive import reactive
from rich.segment import Segment
from rich.style import Style
from textual.strip import Strip
import numpy as np
from collections import deque
import time
import plotext as plt
from typing import Any, Optional


class AudioMeter(Widget):
    """A widget that displays audio input levels over time using plotext,
    with a grey background, filling the widget's width."""

    DEFAULT_CSS = """
    AudioMeter {
        height: 10;
        border: none;
        padding: 0;
        background: #444444; /* a mid-grey color */
    }
    """

    level: reactive[float] = reactive(0.0)
    decay_factor = 0.9

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)
        self.max_level = 0.0
        self.decay = 0.05
        self.history_size = 40
        # Initialize with exact size to prevent resizing artifacts
        self.history = deque([0.0] * self.history_size, maxlen=self.history_size)
        self.max_history = deque([0.0] * self.history_size, maxlen=self.history_size)
        self.time_points = list(range(self.history_size))  # Left to right
        self.last_update = time.time()
        self.update_interval = 0.1
        self._last_level = 0.0
        self._sample_count = 0
        self._level_sum = 0.0
        self._last_logged_level = 0.0
        self._log_threshold = 0.01
        self._dynamic_max = 0.1
        self._max_decay_rate = 0.99
        self._min_level = 0.001
        self._cleanup_threshold = 0.005

        # We'll keep a cached list of strings representing each line of the plot,
        # so we don't rebuild the plot 10 times every frame. This will be set to `None`
        # whenever something changes (e.g. `level` changes).
        self._plot_render_cache: Optional[list[str]] = None

    def update_level(self, audio_data: bytes, format_width: int = 4) -> None:
        """Update the audio level from raw audio data."""
        try:
            current_time = time.time()

            # Convert bytes to numpy array based on format
            if format_width == 4:  # Float32
                samples = np.frombuffer(audio_data, dtype=np.float32)
            elif format_width == 2:  # Int16
                samples = (
                    np.frombuffer(audio_data, dtype=np.int16).astype(np.float32)
                    / 32768.0
                )
            else:
                return

            # Calculate RMS level
            rms = np.sqrt(np.mean(samples**2))
            level = min(1.0, rms * 8.0)  # Amplification factor

            # Accumulate levels
            self._level_sum += level
            self._sample_count += 1

            # Update display periodically
            if current_time - self.last_update >= self.update_interval:
                # Calculate average level
                avg_level = (
                    self._level_sum / self._sample_count
                    if self._sample_count > 0
                    else 0.0
                )

                # Apply smoothing
                smoothing = 0.5
                self.level = smoothing * self._last_level + (1 - smoothing) * avg_level

                # Update dynamic maximum level
                if self.level > self._dynamic_max:
                    self._dynamic_max = self.level
                else:
                    # Faster decay when level is very low
                    if self.level < self._min_level:
                        self._dynamic_max *= 0.95  # Faster decay
                    else:
                        self._dynamic_max *= self._max_decay_rate

                # Keep max level above a minimum threshold
                self._dynamic_max = max(self._dynamic_max, 0.1)

                # Clean up very low levels
                if self.level < self._cleanup_threshold:
                    self.level = 0.0

                # Update histories - shift left and add new value at right
                self.history.rotate(-1)
                self.history[-1] = self.level

                self.max_history.rotate(-1)
                self.max_history[-1] = self._dynamic_max

                # Force complete redraw
                self.refresh(layout=True)  # Force layout recalculation

                self._last_level = self.level

                # Log levels
                if abs(self.level - self._last_logged_level) > self._log_threshold:
                    self.log.debug(
                        f"Audio level: {self.level:.3f} | "
                        f"Dynamic max: {self._dynamic_max:.3f} | "
                        f"RMS: {rms:.3f}"
                    )
                    self._last_logged_level = self.level

                # Reset accumulators
                self._level_sum = 0.0
                self._sample_count = 0
                self.last_update = current_time

                self.refresh()

        except Exception as e:
            self.log.error(f"Error in update_level: {e}")

    def _build_plot(self) -> list[str]:
        """Build the entire plot text once and return it as a list of lines."""
        plt.clear_figure()
        plt.clear_data()

        plot_width = max(self.size.width, 1)
        plot_height = self.size.height

        plt.plotsize(plot_width, plot_height)
        plt.theme("dark")
        plt.grid(False)

        plt.plot(self.time_points, list(self.history), color="white", marker="braille")
        plt.plot(
            self.time_points, list(self.max_history), color="red", marker="braille"
        )

        max_y = max(max(self.max_history), 0.1)
        plt.ylim(0, max_y * 1.2)

        plt.xlabel("")
        plt.ylabel("")
        plt.ticks_color("white")
        plt.frame(False)
        plt.yticks([])
        plt.xticks([])

        # Build & split into lines (strings)
        full_plot = plt.build()
        return (
            full_plot.split("\n") if isinstance(full_plot, str) else []
        )  # Ensure str return type

    def render_line(self, y: int) -> Strip:
        """
        Render exactly one line y. We build (or reuse a cached) plot,
        pick the correct line from it, and center it horizontally.
        """
        try:
            # (Re)build the plot only once per refresh
            if self._plot_render_cache is None:
                self._plot_render_cache = self._build_plot()

            if 0 <= y < len(self._plot_render_cache):
                plot_line = self._plot_render_cache[y]
            else:
                plot_line = ""

            # Trim trailing whitespace from plotext
            plot_line = plot_line.rstrip()

            # We want to center the plot line inside the full widget width.
            line_len = len(plot_line)
            total_width = self.size.width

            # Left offset = half the remaining space, if any
            left_pad = (total_width - line_len) // 2
            if left_pad < 0:
                # If the plot line somehow is longer (shouldn't happen unless widget is too narrow)
                left_pad = 0

            # Build final line with the left offset, then cut/pad to widget width
            line_str = (" " * left_pad) + plot_line
            # Ensure final line is exactly the widget width
            if len(line_str) < total_width:
                line_str = line_str.ljust(total_width)
            elif len(line_str) > total_width:
                line_str = line_str[:total_width]

            return Strip([Segment(line_str, Style())])

        except Exception as e:
            self.log.error(f"Error in render_line: {e}")
            # Fallback: Return an empty line if something fails
            return Strip([Segment(" " * self.size.width, Style())])

    def watch_level(self, old_value: float, new_value: float) -> None:
        """
        Whenever 'level' changes, clear the cached plot so next render_line call
        rebuilds the entire plot (and properly cleans artifacts).
        """
        self._plot_render_cache = None
