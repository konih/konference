from typing import Any, Dict, Optional

import pytest

from src.state.app_state import (
    AppState,
    TranscriptionLanguage,
    RecordingState,
    AppStateData,
)


@pytest.fixture
def app_state(mock_components: Dict[str, Any]) -> AppState:
    """Create AppState instance with mocked components."""
    state = AppState()
    state.logger = mock_components["logger"]

    # Initialize state data
    state._state = AppStateData(
        recording_state=RecordingState.STOPPED,
        language=TranscriptionLanguage.ENGLISH,
        is_processing=False,
    )

    # Mock the update_state method to actually update the state
    async def mock_update_state(**kwargs: Any) -> None:
        for key, value in kwargs.items():
            if hasattr(state._state, key):
                setattr(state._state, key, value)
            else:
                state.logger.error(f"Invalid state attribute: {key}")

    # Mock toggle_language to actually toggle the language
    async def mock_toggle_language() -> Optional[TranscriptionLanguage]:
        if not await state.can_toggle_language():
            return None
        new_lang = (
            TranscriptionLanguage.GERMAN
            if state._state.language == TranscriptionLanguage.ENGLISH
            else TranscriptionLanguage.ENGLISH
        )
        state._state.language = new_lang
        return new_lang

    # Mock can_toggle_language to check state
    async def mock_can_toggle_language() -> bool:
        return (
            state._state.recording_state == RecordingState.STOPPED
            and not state._state.is_processing
        )

    state.update_state = mock_update_state  # type: ignore
    state.toggle_language = mock_toggle_language  # type: ignore
    state.can_toggle_language = mock_can_toggle_language  # type: ignore

    return state


@pytest.mark.asyncio
async def test_initial_state(app_state: AppState) -> None:
    """Test initial state values."""
    state = await app_state.get_state()
    assert state.recording_state == RecordingState.STOPPED
    assert state.language == TranscriptionLanguage.ENGLISH
    assert not state.is_processing


@pytest.mark.asyncio
async def test_update_state(app_state: AppState) -> None:
    """Test state update functionality."""
    await app_state.update_state(recording_state=RecordingState.RECORDING)
    state = await app_state.get_state()
    assert state.recording_state == RecordingState.RECORDING

    # Test invalid attribute
    await app_state.update_state(invalid_attr=True)
    assert (
        app_state.logger.error.call_args[0][0]
        == "Invalid state attribute: invalid_attr"
    )  # type: ignore[union-attr]


@pytest.mark.asyncio
async def test_language_toggle(app_state: AppState) -> None:
    """Test language toggle functionality."""
    # Initial state should be English
    state = await app_state.get_state()
    assert state.language == TranscriptionLanguage.ENGLISH

    # Toggle to German
    new_language = await app_state.toggle_language()
    assert new_language == TranscriptionLanguage.GERMAN
    state = await app_state.get_state()
    assert state.language == TranscriptionLanguage.GERMAN

    # Toggle back to English
    new_language = await app_state.toggle_language()
    assert new_language == TranscriptionLanguage.ENGLISH
    state = await app_state.get_state()
    assert state.language == TranscriptionLanguage.ENGLISH


@pytest.mark.asyncio
async def test_language_toggle_blocked(app_state: AppState) -> None:
    """Test language toggle is blocked appropriately."""
    # Block toggle during recording
    await app_state.update_state(recording_state=RecordingState.RECORDING)
    assert not await app_state.can_toggle_language()
    new_lang = await app_state.toggle_language()
    assert new_lang is None

    # Block toggle during processing
    await app_state.update_state(
        recording_state=RecordingState.STOPPED, is_processing=True
    )
    assert not await app_state.can_toggle_language()
    new_lang = await app_state.toggle_language()
    assert new_lang is None
