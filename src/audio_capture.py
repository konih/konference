import pyaudio
from typing import AsyncGenerator, Optional, Callable, cast
import asyncio
import logging
import numpy as np
from numpy.typing import NDArray


class AudioCapture:
    """Handles audio capture from the system's microphone."""

    def __init__(
        self,
        format: int = pyaudio.paFloat32,
        channels: int = 1,
        rate: int = 16000,
        chunk: int = 1024,
        level_callback: Optional[Callable[[bytes], None]] = None,
        logger: Optional[logging.Logger] = None,
        enabled: bool = False,
    ):
        self.enabled = enabled
        self.format = format
        self.channels = channels
        self.rate = rate
        self.chunk = chunk
        self.audio = pyaudio.PyAudio() if enabled else None
        self.stream: Optional[pyaudio.Stream] = None
        self.level_callback = level_callback
        self._running = False
        self.logger = logger or logging.getLogger(__name__)

    async def start_stream(self) -> AsyncGenerator[bytes, None]:
        """
        Starts capturing audio from the microphone and yields chunks of audio data.
        If audio capture is disabled, yields empty chunks.
        """
        if not self.enabled:
            self.logger.info("Audio capture is disabled")
            while True:
                await asyncio.sleep(0.1)
                yield b"\x00" * self.chunk

        if self.audio is None:
            self.logger.error("PyAudio not initialized")
            while True:
                await asyncio.sleep(0.1)
                yield b"\x00" * self.chunk

        self.logger.debug(
            f"Starting stream with format={self.format}, rate={self.rate}, chunk={self.chunk}"
        )
        self.stream = self.audio.open(
            format=self.format,
            channels=self.channels,
            rate=self.rate,
            input=True,
            frames_per_buffer=self.chunk,
        )
        self._running = True

        last_log = 0.0
        log_interval = 1.0  # Log every second

        while self._running:
            try:
                if self.stream is None:
                    break

                data = self.stream.read(self.chunk, exception_on_overflow=False)
                current_time = asyncio.get_event_loop().time()

                if self.level_callback:
                    try:
                        self.level_callback(data)
                    except Exception as e:
                        self.logger.error(f"Error in level callback: {e}")

                # Log audio capture status periodically with data details
                if current_time - last_log >= log_interval:
                    # Convert bytes to numpy array based on format
                    if self.format == pyaudio.paFloat32:
                        samples = np.frombuffer(data, dtype=np.float32)
                    elif self.format == pyaudio.paInt16:
                        samples = cast(
                            NDArray[np.float32],
                            np.frombuffer(data, dtype=np.int16).astype(np.float32)
                            / 32768.0,
                        )
                    else:
                        samples = np.zeros(
                            0, dtype=np.float32
                        )  # Empty array for unsupported formats

                    if len(samples) > 0:
                        max_sample = float(np.max(np.abs(samples)))
                        rms = float(np.sqrt(np.mean(samples**2)))
                    last_log = current_time

                yield data
                await asyncio.sleep(0.01)
            except Exception as e:
                self.logger.error(f"Error reading audio: {e}")
                break

    async def stop_stream(self) -> None:
        """Stops the audio capture stream and cleans up resources."""
        self._running = False
        if not self.enabled:
            return

        if self.stream:
            self.logger.debug("Stopping audio stream")
            self.stream.stop_stream()
            self.stream.close()
            self.stream = None
        if self.audio:
            self.audio.terminate()
