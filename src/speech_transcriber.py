import azure.cognitiveservices.speech as speechsdk
import os
from typing import AsyncGenerator, Optional
from dotenv import load_dotenv
from src.config import Config
from src.logger import AppLogger
import asyncio


class SpeechTranscriber:
    """Handles speech-to-text transcription using Azure Cognitive Services."""

    def __init__(self, config: Optional[Config] = None):
        load_dotenv()

        self.config = config or Config()
        self.speech_config = speechsdk.SpeechConfig(
            subscription=os.getenv("AZURE_SPEECH_KEY"),
            region=os.getenv("AZURE_SPEECH_REGION"),
        )
        self.audio_config = speechsdk.audio.AudioConfig(use_default_microphone=True)
        self.speech_recognizer = speechsdk.SpeechRecognizer(
            speech_config=self.speech_config, audio_config=self.audio_config
        )
        self.logger = AppLogger().logger
        self.logger.info("Speech transcriber initialized")
        self._running = False
        self._queue: asyncio.Queue[str] = asyncio.Queue()

    async def start_transcription(self) -> AsyncGenerator[str, None]:
        """
        Starts continuous speech recognition and yields transcribed text.
        """
        self._running = True
        done = asyncio.Event()

        def handle_result(evt: speechsdk.SpeechRecognitionEventArgs) -> None:
            if evt.result.reason == speechsdk.ResultReason.RecognizedSpeech:
                text = evt.result.text
                self.logger.debug(f"Speech recognized: {text}")
                asyncio.create_task(self._queue.put(text))
            elif evt.result.reason == speechsdk.ResultReason.NoMatch:
                self.logger.warning(
                    f"No speech could be recognized: {evt.result.no_match_details}"
                )
            elif evt.result.reason == speechsdk.ResultReason.Canceled:
                self.logger.error(
                    f"Speech recognition canceled: {evt.result.cancellation_details}"
                )
                done.set()

        self.speech_recognizer.recognized.connect(handle_result)
        self.speech_recognizer.start_continuous_recognition()
        self.logger.info("Started continuous recognition")

        try:
            while self._running and not done.is_set():
                try:
                    text = await asyncio.wait_for(self._queue.get(), timeout=0.1)
                    yield text
                except asyncio.TimeoutError:
                    continue
                except Exception as e:
                    self.logger.error(f"Error in transcription loop: {e}")
                    break
        finally:
            self.stop_transcription()

    def stop_transcription(self) -> None:
        """Stops the speech recognition process."""
        if self._running:
            self._running = False
            self.speech_recognizer.stop_continuous_recognition()
            self.logger.info("Stopped continuous recognition")
