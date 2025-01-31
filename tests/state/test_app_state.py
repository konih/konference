import pytest
from src.state.app_state import AppState, TranscriptionLanguage, RecordingState
from typing import Any, Dict


@pytest.fixture
def app_state(mock_components: Dict[str, Any]) -> AppState:
    """Create AppState instance with mocked components."""
    state = AppState()
    state.logger = mock_components["logger"]
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
    app_state.logger.error.assert_called_with("Invalid state attribute: invalid_attr")


@pytest.mark.asyncio
async def test_language_toggle_conditions(app_state: AppState) -> None:
    """Test conditions for language toggle."""
    # Should be able to toggle when stopped
    assert await app_state.can_toggle_language()

    # Should not toggle during recording
    await app_state.update_state(recording_state=RecordingState.RECORDING)
    assert not await app_state.can_toggle_language()

    # Should not toggle during processing
    await app_state.update_state(
        recording_state=RecordingState.STOPPED, is_processing=True
    )
    assert not await app_state.can_toggle_language()


@pytest.mark.asyncio
async def test_language_toggle(app_state: AppState) -> None:
    """Test language toggle functionality."""
    # Initial state
    state = await app_state.get_state()
    assert state.language == TranscriptionLanguage.ENGLISH

    # Toggle to German
    new_lang = await app_state.toggle_language()
    assert new_lang == TranscriptionLanguage.GERMAN
    state = await app_state.get_state()
    assert state.language == TranscriptionLanguage.GERMAN

    # Toggle back to English
    new_lang = await app_state.toggle_language()
    assert new_lang == TranscriptionLanguage.ENGLISH
    state = await app_state.get_state()
    assert state.language == TranscriptionLanguage.ENGLISH


@pytest.mark.asyncio
async def test_language_toggle_blocked(app_state: AppState) -> None:
    """Test language toggle is blocked appropriately."""
    # Block toggle during recording
    await app_state.update_state(recording_state=RecordingState.RECORDING)
    new_lang = await app_state.toggle_language()
    assert new_lang is None
    state = await app_state.get_state()
    assert state.language == TranscriptionLanguage.ENGLISH

    # Block toggle during processing
    await app_state.update_state(
        recording_state=RecordingState.STOPPED, is_processing=True
    )
    new_lang = await app_state.toggle_language()
    assert new_lang is None
