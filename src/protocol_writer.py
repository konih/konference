from datetime import datetime
from typing import Optional, TextIO


class ProtocolWriter:
    """Handles writing transcribed text to a protocol file."""

    def __init__(self, output_file: str):
        self.output_file = output_file
        self.file_handle: Optional[TextIO] = None

    def start_protocol(self) -> None:
        """Starts a new protocol session."""
        self.file_handle = open(self.output_file, "w", encoding="utf-8")
        header = f"Protocol - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
        header += "=" * 50 + "\n\n"
        self.file_handle.write(header)

    def write_entry(self, text: str) -> None:
        """Writes a new entry to the protocol."""
        if self.file_handle:
            timestamp = datetime.now().strftime("%H:%M:%S")
            entry = f"[{timestamp}] {text}\n"
            self.file_handle.write(entry)
            self.file_handle.flush()

    def close_protocol(self) -> None:
        """Closes the protocol session."""
        if self.file_handle:
            footer = (
                f"\nProtocol ended - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
            )
            self.file_handle.write(footer)
            self.file_handle.close()
