import pytest
from datetime import datetime
from src.protocol_writer import ProtocolWriter
import os


@pytest.fixture
def protocol_writer():
    test_file = "test_protocol.txt"
    writer = ProtocolWriter(test_file)
    yield writer
    # Cleanup
    if os.path.exists(test_file):
        os.remove(test_file)


def test_protocol_writer_creates_file(protocol_writer):
    protocol_writer.start_protocol()
    assert os.path.exists(protocol_writer.output_file)


def test_protocol_writer_writes_entry(protocol_writer):
    test_text = "Test transcription"
    protocol_writer.start_protocol()
    protocol_writer.write_entry(test_text)

    with open(protocol_writer.output_file, "r", encoding="utf-8") as f:
        content = f.read()
        assert test_text in content
        assert datetime.now().strftime("%Y-%m-%d") in content
