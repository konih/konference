from datetime import datetime
from pathlib import Path

import pytest

from src.markdown_renderer import MarkdownRenderer
from src.meeting_note import MeetingNote


@pytest.fixture
def sample_meeting() -> MeetingNote:
    """Create a sample meeting for testing."""
    meeting = MeetingNote(
        title="Test Meeting",
        start_time=datetime(2024, 1, 1, 10, 0),
        participants=["Alice", "Bob"],
        tags=["important", "test"],
    )
    meeting.raw_text = "This is the raw transcript"
    meeting.summary = "This is a summary"
    meeting.add_content("Note 1")
    meeting.add_content("Note 2")
    return meeting


def test_markdown_render(sample_meeting: MeetingNote) -> None:
    """Test rendering meeting to markdown."""
    markdown = MarkdownRenderer.render(sample_meeting)

    # Check all sections are present
    assert "Test Meeting" in markdown

    # Check content
    assert "Alice, Bob" in markdown
    assert "important, test" in markdown
    assert "This is the raw transcript" in markdown
    assert "This is a summary" in markdown


def test_markdown_save(sample_meeting: MeetingNote, tmp_path: Path) -> None:
    """Test saving meeting as markdown."""
    # Set up
    md_dir = tmp_path / "meetings"
    md_dir.mkdir()

    # Save markdown
    MarkdownRenderer.save_markdown(sample_meeting, str(md_dir))

    # Check file exists and contains content
    md_files = list(md_dir.glob("*.md"))
    assert len(md_files) == 1

    content = md_files[0].read_text()
    assert "# Test Meeting" in content
    assert "This is the raw transcript" in content
