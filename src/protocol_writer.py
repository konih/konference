from datetime import datetime
from typing import Optional, TextIO
from src.meeting_store import MeetingStore


class ProtocolWriter:
    """Handles writing transcribed text to a protocol file."""

    def __init__(self, output_file: str, meeting_store: Optional[MeetingStore] = None):
        self.output_file = output_file
        self.file_handle: Optional[TextIO] = None
        self.meeting_store = meeting_store

    def start_protocol(self) -> None:
        """Starts a new protocol session."""
        self.file_handle = open(self.output_file, "w", encoding="utf-8")
        header = f"Protocol - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
        header += "=" * 50 + "\n\n"
        self.file_handle.write(header)

    def write_entry(self, text: str) -> None:
        """Writes a new entry to the protocol and meeting store."""
        if self.file_handle:
            timestamp = datetime.now().strftime("%H:%M:%S")
            entry = f"[{timestamp}] {text}\n"
            self.file_handle.write(entry)
            self.file_handle.flush()

            # Also add to meeting store if available
            if self.meeting_store:
                self.meeting_store.add_content(entry)

    def close_protocol(self) -> None:
        """Closes the protocol session."""
        if self.file_handle:
            footer = (
                f"\nProtocol ended - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
            )
            self.file_handle.write(footer)
            self.file_handle.close()
