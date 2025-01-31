import asyncio
from dataclasses import dataclass
from enum import Enum
from typing import Optional, Any

from src.logger import AppLogger


class TranscriptionLanguage(Enum):
    """Supported transcription languages."""

    ENGLISH = "en-US"
    GERMAN = "de-DE"


class RecordingState(Enum):
    """Possible states for the recording system."""

    STOPPED = "stopped"
    RECORDING = "recording"
    PAUSED = "paused"


@dataclass
class AppStateData:
    """Data class holding application state."""

    recording_state: RecordingState = RecordingState.STOPPED
    language: TranscriptionLanguage = TranscriptionLanguage.ENGLISH
    is_processing: bool = False
    is_summarizing: bool = False


class AppState:
    """Manages application state with async support."""

    def __init__(self) -> None:
        """Initialize app state."""
        self._state = AppStateData()
        self._lock = asyncio.Lock()
        self.logger = AppLogger().logger

    async def get_state(self) -> AppStateData:
        """Get current state (thread-safe)."""
        async with self._lock:
            return self._state

    async def update_state(self, **kwargs: Any) -> None:
        """Update state attributes (thread-safe)."""
        async with self._lock:
            for key, value in kwargs.items():
                if hasattr(self._state, key):
                    setattr(self._state, key, value)
                    self.logger.debug(f"State updated: {key} = {value}")
                else:
                    self.logger.error(f"Invalid state attribute: {key}")

            # Ensure processing state is properly reset
            if (
                "recording_state" in kwargs
                and kwargs["recording_state"] == RecordingState.STOPPED
            ):
                self._state.is_processing = False

    async def can_toggle_language(self) -> bool:
        """Check if language can be toggled."""
        state = await self.get_state()
        # Only allow toggle when stopped AND not processing
        return state.is_processing

    async def toggle_language(self) -> Optional[TranscriptionLanguage]:
        """Toggle language if possible."""
        if not await self.can_toggle_language():
            return None

        async with self._lock:
            current = self._state.language
            new_language = (
                TranscriptionLanguage.GERMAN
                if current == TranscriptionLanguage.ENGLISH
                else TranscriptionLanguage.ENGLISH
            )
            self._state.language = new_language
            self.logger.info(f"Language switched to: {new_language.value}")
            return new_language

    async def can_generate_summary(self) -> bool:
        """Check if summary can be generated."""
        state = await self.get_state()
        return (
            state.recording_state == RecordingState.STOPPED
            and not state.is_processing
            and not state.is_summarizing
        )

    async def toggle_summarizing(self, value: bool) -> None:
        """Set summarizing state."""
        await self.update_state(is_summarizing=value)
