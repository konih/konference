import pytest
import pytest_asyncio
from unittest.mock import Mock, AsyncMock
from textual.app import App
from textual.widgets import Input, TextArea
from textual._context import active_app
from src.ui.widgets.meeting_form import MeetingForm
from typing import Any, Optional, AsyncGenerator
import asyncio


@pytest.fixture
def test_app_base() -> App[None]:
    """Create a base test app."""
    app = App[None]()
    app._test_screen = Mock()
    app._test_driver = Mock()
    app._test_animator = AsyncMock()
    return app


@pytest_asyncio.fixture
async def test_app(
    test_app_base: App[None], mock_components: dict[str, Any]
) -> AsyncGenerator[MeetingForm, None]:
    """Create and clean up a test form instance."""
    active_app.set(test_app_base)

    form = MeetingForm()
    form._parent = test_app_base

    # Set up mock widgets using centralized mocks
    mock_title = Mock(spec=Input)
    mock_title.value = "Test Meeting"

    mock_participants = Mock(spec=TextArea)
    mock_participants.text = "Alice\nBob"

    mock_tags = Mock(spec=TextArea)
    mock_tags.text = "important\ntest"

    def mock_query_one(selector: str, widget_type: Optional[type] = None) -> Any:
        if selector == "#title":
            return mock_title
        elif selector == "#participants":
            return mock_participants
        elif selector == "#tags":
            return mock_tags
        return Mock()

    form.query_one = mock_query_one
    form.post_message = AsyncMock()

    try:
        yield form
    finally:
        # Clean up any pending tasks
        tasks = [t for t in asyncio.all_tasks() if t is not asyncio.current_task()]
        for task in tasks:
            task.cancel()
            try:
                await task
            except asyncio.CancelledError:
                pass
        active_app.set(None)  # Reset app context


@pytest.mark.asyncio
async def test_meeting_form_creation(test_app: MeetingForm) -> None:
    """Test that the form is created with correct initial values."""
    title_input = test_app.query_one("#title", Input)
    participants_area = test_app.query_one("#participants", TextArea)
    tags_area = test_app.query_one("#tags", TextArea)

    assert title_input.value == "Test Meeting"
    assert participants_area.text == "Alice\nBob"
    assert tags_area.text == "important\ntest"


@pytest.mark.asyncio
async def test_meeting_form_collect_data(test_app: MeetingForm) -> None:
    """Test collecting data from the form."""
    result = test_app.collect_form_data()
    assert result == ("Test Meeting", ["Alice", "Bob"], ["important", "test"])
