import json
import os
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import List, Optional, Dict, Union, Any


@dataclass
class MeetingNote:
    """Represents a meeting note with metadata and content."""

    title: str
    start_time: datetime
    end_time: Optional[datetime] = None
    participants: List[str] = field(default_factory=list)
    tags: List[str] = field(default_factory=list)
    content: List[str] = field(default_factory=list)
    raw_text: str = ""
    summary: str = ""
    file_path: Optional[str] = None
    metadata: Dict[str, Union[str, int, float]] = field(default_factory=dict)

    @property
    def duration(self) -> Optional[timedelta]:
        """Get the duration of the meeting."""
        if self.end_time:
            return self.end_time - self.start_time
        return None

    @property
    def word_count(self) -> int:
        """Get the total word count of the meeting content."""
        return sum(len(text.split()) for text in self.content)

    def add_content(self, text: str) -> None:
        """Add new content to the meeting note."""
        self.content.append(text)
        # No need to update raw_text here as it's handled by MeetingStore

    def _calculate_words_per_minute(self) -> float:
        """Calculate the average words per minute for the meeting."""
        if not self.duration or self.duration.total_seconds() == 0:
            return 0.0
        minutes = self.duration.total_seconds() / 60
        # Round to 2 decimal places to match test expectations
        return round(self.word_count / minutes, 2) if minutes > 0 else 0.0

    def end_meeting(self, end_time: Optional[datetime] = None) -> None:
        """End the meeting and calculate metadata."""
        if end_time is not None:
            self.end_time = end_time
        elif self.end_time is None:
            self.end_time = datetime.now()

        # Calculate metadata
        self.metadata["duration"] = str(self.duration)
        self.metadata["word_count"] = self.word_count
        self.metadata["average_words_per_minute"] = self._calculate_words_per_minute()

    def to_dict(self) -> Dict[str, Any]:
        """Convert the meeting note to a dictionary."""
        return {
            "title": self.title,
            "start_time": self.start_time.isoformat(),
            "end_time": self.end_time.isoformat() if self.end_time else None,
            "participants": self.participants,
            "tags": self.tags,
            "content": self.content,
            "raw_text": self.raw_text,
            "summary": self.summary,
            "metadata": self.metadata,
        }

    def get_summary(self) -> str:
        """Get a summary of the meeting."""
        summary = [
            f"Title: {self.title}",
            f"Date: {self.start_time.strftime('%Y-%m-%d %H:%M')}",
            f"Duration: {self.duration}" if self.duration else "Duration: Ongoing",
            f"Participants: {', '.join(self.participants)}",
            f"Tags: {', '.join(self.tags)}",
            f"Word Count: {self.word_count}",
        ]
        return "\n".join(summary)

    def save(self, directory: str = "meetings") -> None:
        """Save the meeting note to a file."""
        os.makedirs(directory, exist_ok=True)

        # Generate filename if not set
        if not self.file_path:
            timestamp = self.start_time.strftime("%Y%m%d_%H%M%S")
            safe_title = "".join(c if c.isalnum() else "_" for c in self.title)
            self.file_path = os.path.join(directory, f"{timestamp}_{safe_title}.json")

        # Save as JSON
        with open(self.file_path, "w", encoding="utf-8") as f:
            json.dump(self.to_dict(), f, indent=2, ensure_ascii=False)

    @classmethod
    def load(cls, file_path: str) -> "MeetingNote":
        """Load a meeting note from a file."""
        with open(file_path, "r", encoding="utf-8") as f:
            data = json.load(f)

        return cls(
            title=data["title"],
            start_time=datetime.fromisoformat(data["start_time"]),
            end_time=datetime.fromisoformat(data["end_time"])
            if data["end_time"]
            else None,
            participants=data["participants"],
            tags=data["tags"],
            content=data["content"],
            raw_text=data["raw_text"],
            summary=data["summary"],
            file_path=file_path,
            metadata=data.get("metadata", {}),
        )

    def update_file_path(self) -> None:
        """Update the file path based on current title."""
        timestamp = self.start_time.strftime("%Y%m%d_%H%M%S")
        safe_title = "".join(
            c for c in self.title if c.isalnum() or c in (" ", "_")
        ).rstrip()
        safe_title = safe_title.replace(" ", "_")
        self.file_path = f"{timestamp}_{safe_title}.json"
