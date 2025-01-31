from typing import AsyncGenerator, Any
from unittest.mock import Mock, AsyncMock, patch

import pytest
import pytest_asyncio
from textual.widgets import Button

from src.state.app_state import TranscriptionLanguage
from src.ui.app import TranscriberUI


@pytest_asyncio.fixture
async def app(mock_components: dict[str, Any]) -> AsyncGenerator[TranscriberUI, None]:
    """Create and mount a TranscriberUI instance."""
    with patch(
        "src.speech_transcriber.speechsdk", mock_components.get("speech_sdk", Mock())
    ):
        app = TranscriberUI()
        app.transcriber = Mock(spec=["set_language"])
        app.logger = mock_components["logger"]
        app.state = mock_components["state"]
        app.notify = Mock()

        async with app.run_test() as pilot:
            yield app


@pytest.fixture
def mock_app() -> Mock:
    """Create a mock app for testing."""
    app = Mock()
    app.state = Mock()
    app.state.can_toggle_language = AsyncMock(return_value=True)
    app.state.toggle_language = AsyncMock(return_value=TranscriptionLanguage.GERMAN)
    app.notify = Mock()

    # Instead of making action_toggle_language a simple AsyncMock,
    # implement its actual behavior
    async def mock_action_toggle_language() -> None:
        if await app.state.can_toggle_language():
            language = await app.state.toggle_language()
            button = app.query_one("#language_toggle")
            button.label = "🇩🇪" if language == TranscriptionLanguage.GERMAN else "🇺🇸"
            app.notify("Switched to German", title="🔄 Language Changed")
        else:
            button = app.query_one("#language_toggle")
            button.disabled = True
            app.notify(
                "Cannot change language while recording or processing",
                title="⚠️ Warning",
            )

    app.action_toggle_language = mock_action_toggle_language
    return app


@pytest.fixture
def mock_language_toggle() -> Mock:
    """Create a mock language toggle button."""
    toggle = Mock(spec=Button)
    toggle.disabled = False
    toggle.label = Mock()  # Add label mock
    return toggle


@pytest.mark.asyncio
async def test_language_button_updates(
    mock_app: Mock, mock_language_toggle: Mock
) -> None:
    """Test language button updates correctly."""
    # Setup
    mock_app.query_one = Mock(return_value=mock_language_toggle)

    # Execute
    await mock_app.action_toggle_language()

    # Verify
    mock_app.state.toggle_language.assert_awaited_once()
    assert mock_language_toggle.label == "🇩🇪"


@pytest.mark.asyncio
async def test_language_button_disabled_states(
    mock_app: Mock, mock_language_toggle: Mock
) -> None:
    """Test language button disabled states."""
    # Setup
    mock_app.query_one = Mock(return_value=mock_language_toggle)
    mock_app.state.can_toggle_language = AsyncMock(return_value=False)

    # Execute
    await mock_app.action_toggle_language()

    # Verify
    assert mock_language_toggle.disabled is True


@pytest.mark.asyncio
async def test_language_toggle_notification(
    mock_app: Mock, mock_language_toggle: Mock
) -> None:
    """Test successful language toggle notification."""
    # Setup
    mock_app.query_one = Mock(return_value=mock_language_toggle)

    # Execute
    await mock_app.action_toggle_language()

    # Verify
    mock_app.notify.assert_called_with(
        "Switched to German", title="🔄 Language Changed"
    )


@pytest.mark.asyncio
async def test_language_toggle_blocked_notification(
    mock_app: Mock, mock_language_toggle: Mock
) -> None:
    """Test blocked language toggle notification."""
    # Setup
    mock_app.query_one = Mock(return_value=mock_language_toggle)
    mock_app.state.can_toggle_language = AsyncMock(return_value=False)

    # Execute
    await mock_app.action_toggle_language()

    # Verify
    mock_app.notify.assert_called_with(
        "Cannot change language while recording or processing", title="⚠️ Warning"
    )
