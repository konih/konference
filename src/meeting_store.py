import logging
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional

from src.meeting_note import MeetingNote


class MeetingStore:
    """Manages storage and retrieval of meeting notes."""

    def __init__(
        self, storage_dir: str = "meetings", default_participant: Optional[str] = None
    ) -> None:
        self.storage_dir = Path(storage_dir)
        self.storage_dir.mkdir(exist_ok=True)
        self.current_meeting: Optional[MeetingNote] = None
        self.cached_meetings: Dict[str, MeetingNote] = {}
        self.logger = logging.getLogger(__name__)
        self.default_participant = default_participant

    def create_meeting(
        self,
        title: str = "Untitled Meeting",
        participants: Optional[List[str]] = None,
        tags: Optional[List[str]] = None,
    ) -> MeetingNote:
        """Create a new meeting and set it as current."""
        # Add default participant if provided and not in participants
        meeting_participants = participants or []
        if (
            self.default_participant
            and self.default_participant not in meeting_participants
        ):
            meeting_participants.append(self.default_participant)

        # Create new meeting
        meeting = MeetingNote(
            title=title,
            participants=meeting_participants,  # Use the processed list
            tags=tags or [],  # Ensure tags is a list
            start_time=datetime.now(),
        )

        # Set as current meeting
        self.current_meeting = meeting
        return meeting

    def add_content(self, text: str) -> None:
        """Add content to the current meeting."""
        if self.current_meeting is None:
            self.logger.warning("No active meeting to add content to")
            return

        try:
            text_stripped = text.strip()
            if not text_stripped:
                return

            self.logger.debug(f"Adding content to meeting: {text_stripped}")

            # Add to raw text
            if not self.current_meeting.raw_text:
                self.current_meeting.raw_text = text_stripped
            else:
                self.current_meeting.raw_text += f"\n{text_stripped}"

            # Add to structured content if it ends with punctuation
            if text_stripped.endswith((".", "!", "?")):
                self.current_meeting.content.append(text_stripped)
                self.logger.debug(f"Added complete sentence: {text_stripped}")

            # Save to disk
            self.current_meeting.save()

            self.logger.debug(
                f"Meeting updated - Raw text: {len(self.current_meeting.raw_text)} chars, "
                f"Content: {len(self.current_meeting.content)} items"
            )
        except Exception as e:
            self.logger.error(f"Error adding content: {e}", exc_info=True)

    def end_current_meeting(self) -> None:
        """End the current meeting and save it."""
        if self.current_meeting is not None:
            self.current_meeting.end_meeting()
            self.save_meeting(self.current_meeting)
            self.current_meeting = None

    def save_meeting(self, meeting: MeetingNote) -> None:
        """Save a meeting to storage."""
        try:
            meeting.save(str(self.storage_dir))
            if meeting.file_path is not None:  # Add type check
                self.cached_meetings[meeting.file_path] = meeting
                self.logger.info(f"Saved meeting: {meeting.file_path}")
        except Exception as e:
            self.logger.error(f"Error saving meeting: {e}")

    def load_meeting(self, file_path: str) -> Optional[MeetingNote]:
        """Load a meeting from storage."""
        if file_path in self.cached_meetings:
            return self.cached_meetings[file_path]

        try:
            meeting = MeetingNote.load(file_path)
            self.cached_meetings[file_path] = meeting
            return meeting
        except Exception as e:
            self.logger.error(f"Error loading meeting: {e}")
            return None

    def list_meetings(self) -> List[MeetingNote]:
        """List all available meetings."""
        meetings = []
        for file_path in self.storage_dir.glob("*.json"):
            if meeting := self.load_meeting(str(file_path)):
                meetings.append(meeting)
        return sorted(meetings, key=lambda m: m.start_time, reverse=True)

    def search_meetings(self, query: str) -> List[MeetingNote]:
        """Search meetings by title, participants, or tags."""
        query = query.lower()
        results = []

        for meeting in self.list_meetings():
            if (
                query in meeting.title.lower()
                or any(query in p.lower() for p in meeting.participants)
                or any(query in t.lower() for t in meeting.tags)
                or any(query in c.lower() for c in meeting.content)
            ):
                results.append(meeting)

        return results

    def update_current_meeting(
        self,
        title: str,
        participants: Optional[List[str]] = None,
        tags: Optional[List[str]] = None,
    ) -> None:
        """Update the current meeting with new details."""
        if not self.current_meeting:
            self.logger.error("No current meeting to update")
            return

        self.logger.debug(f"Updating meeting: {self.current_meeting.title} -> {title}")

        # Update the meeting
        self.current_meeting.title = title
        self.current_meeting.participants = participants or []
        self.current_meeting.tags = tags or []

        # Save the changes
        self.current_meeting.save()
        self.logger.debug("Meeting updated and saved")
