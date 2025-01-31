from typing import Tuple, List, Any, Optional, cast, AsyncGenerator
from unittest.mock import Mock, AsyncMock

import pytest
import pytest_asyncio
import pyaudio

from src.ui.app import TranscriberUI

pytestmark = [pytest.mark.asyncio, pytest.mark.meetings]


@pytest_asyncio.fixture
async def mock_app_with_form(mock_app: TranscriberUI) -> AsyncGenerator[TranscriberUI, None]:
    """Extend mock_app with form handling capabilities."""
    async def handle_form_result(
        result: Optional[Tuple[str, List[str], List[str]]]
    ) -> None:
        if result is None:
            return
            
        title, participants, tags = result
        if mock_app.meeting_store.current_meeting is None:
            mock_app.meeting_store.create_meeting(
                title=title,
                participants=participants,
                tags=tags
            )
        else:
            current_meeting = mock_app.meeting_store.current_meeting
            current_meeting.title = title
            current_meeting.participants = participants
            current_meeting.tags = tags
            current_meeting.save()

    mock_app._handle_form_result = AsyncMock(side_effect=handle_form_result)
    yield mock_app


@pytest.mark.asyncio
async def test_meeting_form_workflow(mock_app_with_form: TranscriberUI) -> None:
    """Test the complete meeting form workflow."""
    mock_store = cast(Mock, mock_app_with_form.meeting_store)
    
    # Mock the form submission with AsyncMock
    mock_app_with_form.show_meeting_form = AsyncMock(
        return_value=("Test Meeting", ["Alice"], ["important"])
    )
    mock_app_with_form.meeting_store.current_meeting = None

    form_result = await mock_app_with_form.show_meeting_form()
    await mock_app_with_form._handle_form_result(form_result)

    mock_store.create_meeting.assert_called_once_with(
        title="Test Meeting", participants=["Alice"], tags=["important"]
    )


async def test_form_result_edit_meeting(mock_app_with_form: TranscriberUI) -> None:
    """Test that form result updates existing meeting correctly."""
    # Set up mock current meeting
    current_meeting = Mock()
    current_meeting.title = "Old Title"
    current_meeting.participants = ["Charlie"]
    current_meeting.tags = ["old"]
    mock_app_with_form.meeting_store.current_meeting = current_meeting

    # Mock form submission with AsyncMock
    mock_app_with_form.show_meeting_form = AsyncMock(
        return_value=("New Title", ["Alice", "Bob"], ["important"])
    )

    # Show form and handle result
    form_result = await mock_app_with_form.show_meeting_form()
    await mock_app_with_form._handle_form_result(form_result)

    # Verify meeting was updated
    assert mock_app_with_form.meeting_store.current_meeting.title == "New Title"
    assert mock_app_with_form.meeting_store.current_meeting.participants == ["Alice", "Bob"]
    assert mock_app_with_form.meeting_store.current_meeting.tags == ["important"]
    mock_app_with_form.meeting_store.current_meeting.save.assert_called_once()


async def test_form_result_cancelled(mock_app_with_form: TranscriberUI) -> None:
    """Test that cancelling form submission doesn't change meeting."""
    # Set up mock current meeting
    current_meeting = Mock()
    current_meeting.title = "Old Title"
    current_meeting.participants = ["Charlie"]
    current_meeting.tags = ["old"]
    mock_app_with_form.meeting_store.current_meeting = current_meeting

    # Mock form submission with AsyncMock
    mock_app_with_form.show_meeting_form = AsyncMock(return_value=None)

    # Show form and handle cancelled result
    form_result = await mock_app_with_form.show_meeting_form()
    await mock_app_with_form._handle_form_result(form_result)

    # Verify meeting was not changed
    assert mock_app_with_form.meeting_store.current_meeting.title == "Old Title"
    assert mock_app_with_form.meeting_store.current_meeting.participants == ["Charlie"]
    assert mock_app_with_form.meeting_store.current_meeting.tags == ["old"]
    mock_app_with_form.meeting_store.current_meeting.save.assert_not_called()


# ... more meeting-related tests ...
