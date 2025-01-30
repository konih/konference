import pyaudio
from typing import AsyncGenerator, Optional, Callable, Any
import asyncio


class AudioCapture:
    """Handles audio capture from the system's microphone."""

    def __init__(
        self,
        format: int = pyaudio.paFloat32,
        channels: int = 1,
        rate: int = 16000,
        chunk: int = 1024,
        level_callback: Optional[Callable[[bytes], None]] = None,
        logger: Optional[Any] = None,
    ):
        self.format = format
        self.channels = channels
        self.rate = rate
        self.chunk = chunk
        self.audio = pyaudio.PyAudio()
        self.stream: Optional[pyaudio.Stream] = None
        self.level_callback = level_callback
        self._running = False
        self.logger = logger

    def start_stream(self) -> AsyncGenerator[bytes, None]:
        """
        Starts capturing audio from the microphone and yields chunks of audio data.
        """
        self.logger.debug(f"Starting stream with callback: {self.level_callback is not None}")
        self.stream = self.audio.open(
            format=self.format,
            channels=self.channels,
            rate=self.rate,
            input=True,
            frames_per_buffer=self.chunk,
        )
        self._running = True

        async def audio_generator():
            while self._running:
                try:
                    data = self.stream.read(self.chunk, exception_on_overflow=False)
                    if self.level_callback:
                        try:
                            self.level_callback(data)
                        except Exception as e:
                            self.logger.error(f"Error in level callback: {e}")
                    yield data
                    await asyncio.sleep(0.01)
                except Exception as e:
                    self.logger.error(f"Error reading audio: {e}")
                    break

        return audio_generator()

    def stop_stream(self) -> None:
        """Stops the audio capture stream and cleans up resources."""
        self._running = False
        if self.stream:
            self.stream.stop_stream()
            self.stream.close()
            self.stream = None
        self.audio.terminate()
