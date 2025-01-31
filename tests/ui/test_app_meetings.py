import pytest
from typing import Tuple, List, Any, Optional
from src.ui.app import TranscriberUI

pytestmark = [pytest.mark.asyncio, pytest.mark.meetings]


@pytest.mark.asyncio
async def test_meeting_form_workflow(app: TranscriberUI) -> None:
    """Test the complete meeting form workflow."""

    # Mock the form submission
    async def mock_show_form(
        *args: Any, **kwargs: Any
    ) -> Optional[Tuple[str, List[str], List[str]]]:
        return "Test Meeting", ["Alice"], ["important"]

    # Replace the show_meeting_form method with our mock
    app.show_meeting_form = mock_show_form  # type: ignore[assignment]

    # Get initial content widget state
    meeting_content = app.query_one("#meeting-content")
    assert meeting_content.styles.display == "block"

    # Create a new meeting directly
    app.meeting_store.current_meeting = None

    # Simulate form submission
    form_result = await app.show_meeting_form()
    if form_result is not None:  # Add type check to satisfy mypy
        await app._handle_form_result(form_result)

    # Verify meeting was created with correct values
    app.meeting_store.create_meeting.assert_called_once_with(  # type: ignore[attr-defined]
        title="Test Meeting", participants=["Alice"], tags=["important"]
    )


async def test_form_result_edit_meeting(app: TranscriberUI) -> None:
    """Test that form result updates existing meeting correctly."""
    # Set up mock current meeting
    current_meeting = app.meeting_store.current_meeting
    assert current_meeting is not None

    current_meeting.title = "Old Title"
    current_meeting.participants = ["Charlie"]
    current_meeting.tags = ["old"]

    # Mock form submission for editing
    async def mock_show_form(
        *args: Any, **kwargs: Any
    ) -> Optional[Tuple[str, List[str], List[str]]]:
        return "New Title", ["Alice", "Bob"], ["important"]

    app.show_meeting_form = mock_show_form  # type: ignore[assignment]

    # Show form and handle result
    form_result = await app.show_meeting_form()
    await app._handle_form_result(form_result)

    # Verify meeting was updated
    assert current_meeting.title == "New Title"
    assert current_meeting.participants == ["Alice", "Bob"]
    assert current_meeting.tags == ["important"]
    current_meeting.save.assert_called_once()  # type: ignore[attr-defined]


async def test_form_result_cancelled(app: TranscriberUI) -> None:
    """Test that cancelling form submission doesn't change meeting."""
    # Set up mock current meeting
    current_meeting = app.meeting_store.current_meeting
    assert current_meeting is not None

    current_meeting.title = "Old Title"
    current_meeting.participants = ["Charlie"]
    current_meeting.tags = ["old"]

    # Mock form submission that returns None (cancelled)
    async def mock_show_form(
        *args: Any, **kwargs: Any
    ) -> Optional[Tuple[str, List[str], List[str]]]:
        return None

    app.show_meeting_form = mock_show_form  # type: ignore[assignment]

    # Show form and handle cancelled result
    form_result = await app.show_meeting_form()
    await app._handle_form_result(form_result)

    # Verify meeting was not changed
    assert current_meeting.title == "Old Title"
    assert current_meeting.participants == ["Charlie"]
    assert current_meeting.tags == ["old"]
    current_meeting.save.assert_not_called()  # type: ignore[attr-defined]


# ... more meeting-related tests ...
