import pyaudio
from typing import Generator, Optional, Callable


class AudioCapture:
    """Handles audio capture from the system's microphone."""

    def __init__(
        self,
        format: int = pyaudio.paFloat32,
        channels: int = 1,
        rate: int = 16000,
        chunk: int = 1024,
        level_callback: Optional[Callable[[bytes], None]] = None,
    ):
        self.format = format
        self.channels = channels
        self.rate = rate
        self.chunk = chunk
        self.audio = pyaudio.PyAudio()
        self.stream: Optional[pyaudio.Stream] = None
        self.level_callback = level_callback

    def start_stream(self) -> Generator[bytes, None, None]:
        """
        Starts capturing audio from the microphone and yields chunks of audio data.
        """
        self.stream = self.audio.open(
            format=self.format,
            channels=self.channels,
            rate=self.rate,
            input=True,
            frames_per_buffer=self.chunk,
        )

        try:
            while True:
                data = self.stream.read(self.chunk)
                if self.level_callback:
                    self.level_callback(data)
                yield data
        except KeyboardInterrupt:
            self.stop_stream()

    def stop_stream(self) -> None:
        """Stops the audio capture stream and cleans up resources."""
        if self.stream:
            self.stream.stop_stream()
            self.stream.close()
        self.audio.terminate()
