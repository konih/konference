import os
from datetime import datetime
from pathlib import Path
from typing import Generator

import pytest
from pytest import FixtureRequest

from src.protocol_writer import ProtocolWriter


@pytest.fixture(scope="function")
def protocol_writer(
    request: FixtureRequest, tmp_path: Path
) -> Generator[ProtocolWriter, None, None]:
    """Create a protocol writer with a temporary file."""
    test_file = tmp_path / "test_protocol.txt"
    writer = ProtocolWriter(str(test_file))
    yield writer
    # Cleanup happens automatically with tmp_path


def test_protocol_writer_creates_file(protocol_writer: ProtocolWriter) -> None:
    """Test file creation."""
    protocol_writer.start_protocol()
    assert os.path.exists(protocol_writer.output_file)


def test_protocol_writer_writes_entry(protocol_writer: ProtocolWriter) -> None:
    """Test writing an entry."""
    test_text = "Test transcription"
    protocol_writer.start_protocol()
    protocol_writer.write_entry(test_text)

    with open(protocol_writer.output_file, "r", encoding="utf-8") as f:
        content = f.read()
        assert test_text in content
        assert datetime.now().strftime("%Y-%m-%d") in content


def test_protocol_writer_close(protocol_writer: ProtocolWriter) -> None:
    """Test closing the protocol."""
    protocol_writer.start_protocol()
    protocol_writer.write_entry("Test entry")
    protocol_writer.close_protocol()

    with open(protocol_writer.output_file, "r", encoding="utf-8") as f:
        content = f.read()
        assert "Protocol ended" in content


def test_protocol_writer_multiple_entries(protocol_writer: ProtocolWriter) -> None:
    """Test writing multiple entries."""
    entries = ["Entry 1", "Entry 2", "Entry 3"]
    protocol_writer.start_protocol()

    for entry in entries:
        protocol_writer.write_entry(entry)

    with open(protocol_writer.output_file, "r", encoding="utf-8") as f:
        content = f.read()
        for entry in entries:
            assert entry in content


def test_protocol_writer_header_format(protocol_writer: ProtocolWriter) -> None:
    """Test protocol header format."""
    protocol_writer.start_protocol()
    if protocol_writer.file_handle is not None:  # Add null check
        protocol_writer.file_handle.flush()

    with open(protocol_writer.output_file, "r", encoding="utf-8") as f:
        content = f.read()
        assert "Protocol - " in content
        assert "=" * 50 in content
