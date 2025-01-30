import azure.cognitiveservices.speech as speechsdk
import os
from typing import Generator, Optional
from dotenv import load_dotenv
from src.config import Config


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

    def start_transcription(self) -> Generator[str, None, None]:
        """
        Starts continuous speech recognition and yields transcribed text.
        """
        done = False
        text_queue = []

        def handle_result(evt: speechsdk.SpeechRecognitionEventArgs) -> None:
            nonlocal done
            if evt.result.reason == speechsdk.ResultReason.RecognizedSpeech:
                text_queue.append(evt.result.text)
            elif evt.result.reason == speechsdk.ResultReason.NoMatch:
                print(f"No speech could be recognized: {evt.result.no_match_details}")
            elif evt.result.reason == speechsdk.ResultReason.Canceled:
                print(f"Speech recognition canceled: {evt.result.cancellation_details}")
                done = True

        self.speech_recognizer.recognized.connect(handle_result)
        self.speech_recognizer.start_continuous_recognition()

        try:
            while not done:
                if text_queue:
                    yield text_queue.pop(0)
        except KeyboardInterrupt:
            self.stop_transcription()
            return

    def stop_transcription(self) -> None:
        """Stops the speech recognition process."""
        self.speech_recognizer.stop_continuous_recognition()
