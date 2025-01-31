import azure.cognitiveservices.speech as speechsdk
import os
from typing import Optional
from dotenv import load_dotenv
from src.config import Config
from src.logger import AppLogger
import asyncio
import queue
from queue import Queue
from src.state.app_state import TranscriptionLanguage


class SpeechTranscriber:
    """Handles speech-to-text transcription using Azure Cognitive Services."""

    def __init__(self, config: Optional[Config] = None):
        load_dotenv()

        self.config = config or Config()
        speech_config = self.config.get_speech_config()

        self.speech_config = speechsdk.SpeechConfig(
            subscription=speech_config.get("subscription")
            or os.getenv("AZURE_SPEECH_KEY"),
            region=speech_config.get("region") or os.getenv("AZURE_SPEECH_REGION"),
        )
        self.audio_config = speechsdk.audio.AudioConfig(use_default_microphone=True)
        self.speech_recognizer = speechsdk.SpeechRecognizer(
            speech_config=self.speech_config, audio_config=self.audio_config
        )
        self.logger = AppLogger().logger
        self.logger.info("Speech transcriber initialized")

        # Controls whether continuous recognition is active
        self._running = False
        # Thread-safe queue for the Azure callback
        self._thread_queue: Queue[str] = Queue()
        # Asyncio queue for the consumer
        self._async_queue: asyncio.Queue[str] = asyncio.Queue()
        # Background task for queue transfer
        self._transfer_task: Optional[asyncio.Task] = None

        # Set initial language
        self.speech_config.speech_recognition_language = (
            TranscriptionLanguage.ENGLISH.value
        )

    def get_transcript_queue(self) -> asyncio.Queue[str]:
        """Expose the transcript queue to other components."""
        return self._async_queue

    def start_transcription(self) -> None:
        """Begin continuous speech recognition (non-async)."""
        if self._running:
            return  # Already running

        self._running = True
        self._thread_queue = queue.Queue()  # Create fresh queues
        self._async_queue = asyncio.Queue()

        def handle_result(evt: speechsdk.SpeechRecognitionEventArgs) -> None:
            """Handle speech recognition results."""
            if evt.result.reason == speechsdk.ResultReason.RecognizedSpeech:
                text = evt.result.text
                self.logger.info(f"Speech recognized: {text}")
                try:
                    # Put text in thread-safe queue
                    self._thread_queue.put(text)
                except Exception as e:
                    self.logger.error(f"Error queueing text: {e}", exc_info=True)
            elif evt.result.reason == speechsdk.ResultReason.NoMatch:
                self.logger.warning(
                    f"No speech could be recognized: {evt.result.no_match_details}"
                )
            elif evt.result.reason == speechsdk.ResultReason.Canceled:
                self.logger.error(
                    f"Speech recognition canceled: {evt.result.cancellation_details}"
                )
                self._running = False

        # Start the queue transfer task
        loop = asyncio.get_event_loop()
        self._transfer_task = loop.create_task(self._transfer_queues())

        self.speech_recognizer.recognized.connect(handle_result)
        self.speech_recognizer.start_continuous_recognition_async()
        self.logger.info("Started continuous recognition")

    async def _transfer_queues(self) -> None:
        """Transfer items from thread queue to async queue."""
        while self._running:
            try:
                # Check thread queue with timeout
                try:
                    text = self._thread_queue.get_nowait()
                    await self._async_queue.put(text)
                except queue.Empty:
                    await asyncio.sleep(0.1)  # Short sleep before next check
                    continue
            except Exception as e:
                self.logger.error(
                    f"Error transferring between queues: {e}", exc_info=True
                )
                await asyncio.sleep(0.1)  # Sleep on error before retry

    async def stop_transcription(self) -> None:
        """Stop continuous speech recognition."""
        if not self._running:
            return
        self._running = False
        self.speech_recognizer.stop_continuous_recognition_async()

        # Cancel the transfer task
        if self._transfer_task:
            self._transfer_task.cancel()
            try:
                await self._transfer_task
            except asyncio.CancelledError:
                pass

        self.logger.info("Stopped continuous recognition")

    def set_language(self, language: TranscriptionLanguage) -> None:
        """Update the speech recognition language."""
        self.speech_config.speech_recognition_language = language.value
        self.logger.info(f"Speech recognition language set to: {language.value}")

        # Recreate speech recognizer with new config
        self.speech_recognizer = speechsdk.SpeechRecognizer(
            speech_config=self.speech_config, audio_config=self.audio_config
        )
