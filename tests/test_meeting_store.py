import os
from datetime import datetime
from pathlib import Path

import pytest

from src.meeting_note import MeetingNote
from src.meeting_store import MeetingStore


@pytest.fixture
def meeting_store(tmp_path: Path) -> MeetingStore:
    """Create a test meeting store."""
    store = MeetingStore(storage_dir=str(tmp_path / "meetings"))
    return store


@pytest.fixture
def sample_meeting() -> MeetingNote:
    """Create a sample meeting for testing."""
    return MeetingNote(
        title="Test Meeting",
        start_time=datetime(2024, 1, 1, 10, 0),
        participants=["Alice", "Bob"],
        tags=["important", "test"],
    )


def test_create_meeting(meeting_store: MeetingStore) -> None:
    """Test creating a new meeting."""
    meeting = meeting_store.create_meeting(
        "Test Meeting", participants=["Alice", "Bob"], tags=["test"]
    )

    assert meeting_store.current_meeting == meeting
    assert meeting.title == "Test Meeting"
    assert meeting.participants == ["Alice", "Bob"]
    assert meeting.tags == ["test"]


def test_add_content(meeting_store: MeetingStore) -> None:
    """Test adding content to a meeting."""
    meeting = meeting_store.create_meeting("Test Meeting")
    test_content = "Test content."  # Add period to make it a complete sentence
    meeting_store.add_content(test_content)

    assert meeting_store.current_meeting is not None
    assert meeting_store.current_meeting.raw_text == test_content
    assert len(meeting_store.current_meeting.content) == 1
    assert meeting_store.current_meeting.content[0] == test_content.strip()


def test_end_current_meeting(meeting_store: MeetingStore) -> None:
    """Test ending the current meeting."""
    meeting = meeting_store.create_meeting("Test Meeting")
    meeting_store.add_content("Test content")
    meeting_store.end_current_meeting()

    assert meeting_store.current_meeting is None
    assert meeting.end_time is not None
    assert meeting.file_path is not None
    assert os.path.exists(meeting.file_path)


def test_save_and_load_meeting(
    meeting_store: MeetingStore, sample_meeting: MeetingNote
) -> None:
    # Save meeting
    meeting_store.save_meeting(sample_meeting)
    assert sample_meeting.file_path is not None

    # Load meeting
    loaded_meeting = meeting_store.load_meeting(sample_meeting.file_path)
    assert loaded_meeting is not None
    assert loaded_meeting.title == sample_meeting.title
    assert loaded_meeting.participants == sample_meeting.participants


def test_list_meetings(meeting_store: MeetingStore) -> None:
    """Test listing all meetings."""
    # Create and save multiple meetings
    meeting1 = meeting_store.create_meeting("Meeting 1")
    meeting_store.save_meeting(meeting1)

    meeting2 = meeting_store.create_meeting("Meeting 2")
    meeting_store.save_meeting(meeting2)

    meetings = meeting_store.list_meetings()
    assert len(meetings) == 2
    assert all(isinstance(m, MeetingNote) for m in meetings)


def test_search_meetings(meeting_store: MeetingStore) -> None:
    """Test searching meetings."""
    # Create some test meetings
    meeting1 = meeting_store.create_meeting(
        title="Client Meeting", participants=["Alice", "Bob"], tags=["important"]
    )
    meeting1.add_content("demo content")
    meeting_store.save_meeting(meeting1)

    meeting2 = meeting_store.create_meeting(
        title="Team Standup", participants=["Charlie"], tags=["routine"]
    )
    meeting2.add_content("standup notes")
    meeting_store.save_meeting(meeting2)

    # Search by title
    results = meeting_store.search_meetings("Client")
    assert len(results) == 1
    assert results[0].title == "Client Meeting"

    # Search by content
    results = meeting_store.search_meetings("demo")
    assert len(results) == 1
    assert results[0].title == "Client Meeting"


def test_caching(meeting_store: MeetingStore, sample_meeting: MeetingNote) -> None:
    # Save meeting
    meeting_store.save_meeting(sample_meeting)
    assert sample_meeting.file_path is not None

    # Load meeting twice
    meeting1 = meeting_store.load_meeting(sample_meeting.file_path)
    meeting2 = meeting_store.load_meeting(sample_meeting.file_path)

    assert meeting1 is not None and meeting2 is not None
    # Should be the same object (cached)
    assert meeting1 is meeting2


def test_add_content_without_meeting(meeting_store: MeetingStore) -> None:
    """Test adding content when no meeting is active."""
    # Should not raise an error, just log a warning
    meeting_store.add_content("Test content")
    assert meeting_store.current_meeting is None


def test_create_sample_meeting(tmp_path: Path) -> None:
    """Test creating a sample meeting during initialization."""
    # Create store with sample meeting
    store = MeetingStore(storage_dir=str(tmp_path / "meetings"), create_sample=True)

    # Verify the current meeting is set
    assert store.current_meeting is not None
    assert store.current_meeting.title == "Team Standup"
    assert store.current_meeting.participants == ["Alice", "Bob", "Charlie"]
    assert store.current_meeting.tags == ["standup", "development"]

    # Verify content was properly set
    assert len(store.current_meeting.content) == 10  # 10 sample messages
    assert (
        store.current_meeting.content[0]
        == "Alice: Good morning everyone! Let's go through our updates."
    )

    # Verify raw text was properly joined
    assert "\n" in store.current_meeting.raw_text
    assert store.current_meeting.raw_text.startswith("Alice: Good morning")
    assert store.current_meeting.raw_text.endswith("Great progress everyone!")

    # Verify the meeting was saved to disk
    assert store.current_meeting.file_path is not None
    assert Path(store.current_meeting.file_path).exists()

    # Create store without sample meeting
    store_no_sample = MeetingStore(
        storage_dir=str(tmp_path / "meetings2"), create_sample=False
    )
    assert store_no_sample.current_meeting is None
