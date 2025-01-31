from datetime import datetime, timedelta
import pytest
import os
from src.meeting_note import MeetingNote
from pathlib import Path


@pytest.fixture
def sample_meeting() -> MeetingNote:
    """Create a sample meeting for testing."""
    return MeetingNote(
        title="Test Meeting",
        start_time=datetime(2024, 1, 1, 10, 0),
        participants=["Alice", "Bob"],
        tags=["important", "test"],
    )


def test_meeting_note_creation(sample_meeting: MeetingNote) -> None:
    """Test meeting note creation with default values."""
    assert sample_meeting.title == "Test Meeting"
    assert sample_meeting.participants == ["Alice", "Bob"]
    assert sample_meeting.tags == ["important", "test"]
    assert sample_meeting.content == []
    assert sample_meeting.end_time is None


def test_add_content(sample_meeting: MeetingNote) -> None:
    """Test adding content to a meeting note."""
    sample_meeting.add_content("Test content")
    assert len(sample_meeting.content) == 1
    assert sample_meeting.content[0] == "Test content"


def test_end_meeting(sample_meeting: MeetingNote) -> None:
    """Test ending a meeting."""
    # Set both start and end time to ensure consistent duration
    test_start = datetime(2024, 1, 1, 10, 0)
    test_end = datetime(2024, 1, 1, 11, 0)

    # Create a new meeting with controlled timestamps
    test_meeting = MeetingNote(
        title="Test Meeting",
        start_time=test_start,
        participants=["Alice", "Bob"],
        tags=["important", "test"],
    )
    test_meeting.add_content("Test content")  # 2 words
    test_meeting.end_time = test_end
    test_meeting.end_meeting()

    # Verify results
    assert test_meeting.end_time == test_end
    assert test_meeting.duration == timedelta(hours=1)
    assert test_meeting.word_count == 2  # "Test content" has 2 words
    assert test_meeting.metadata["duration"] == str(timedelta(hours=1))
    assert test_meeting.metadata["word_count"] == 2
    assert (
        test_meeting.metadata["average_words_per_minute"] == 0.03
    )  # Rounded value of 2/60


def test_get_summary(sample_meeting: MeetingNote) -> None:
    """Test getting meeting summary."""
    sample_meeting.add_content("Test content")
    summary = sample_meeting.get_summary()

    assert "Test Meeting" in summary
    assert "2024-01-01 10:00" in summary
    assert "Alice, Bob" in summary
    assert "important, test" in summary


def test_save_and_load(sample_meeting: MeetingNote, tmp_path: Path) -> None:
    """Test saving and loading meeting notes."""
    # Save meeting
    test_dir = tmp_path / "test_meetings"
    sample_meeting.save(str(test_dir))
    assert sample_meeting.file_path is not None
    assert os.path.exists(sample_meeting.file_path)

    # Load meeting
    loaded_meeting = MeetingNote.load(sample_meeting.file_path)
    assert loaded_meeting.title == sample_meeting.title
    assert loaded_meeting.participants == sample_meeting.participants
    assert loaded_meeting.tags == sample_meeting.tags
    assert loaded_meeting.start_time == sample_meeting.start_time


def test_to_dict(sample_meeting: MeetingNote) -> None:
    """Test converting meeting note to dictionary."""
    sample_meeting.add_content("Test content")
    data = sample_meeting.to_dict()

    assert data["title"] == "Test Meeting"
    assert data["participants"] == ["Alice", "Bob"]
    assert data["tags"] == ["important", "test"]
    assert data["content"] == ["Test content"]
    assert data["metadata"] == {}  # Empty until meeting is ended


def test_word_count(sample_meeting: MeetingNote) -> None:
    """Test word count calculation."""
    sample_meeting.add_content("This is a test")
    sample_meeting.add_content("Another test message")
    assert sample_meeting.word_count == 7
