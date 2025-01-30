import pytest
from pathlib import Path
import os
from src.config import Config
import yaml
import shutil


@pytest.fixture
def temp_config_file(tmp_path: Path) -> Path:
    """Create a temporary config file for testing."""
    config_data = {
        "paths": {
            "logs": "test_logs",
            "meetings": "test_meetings",
            "screenshots": "test_screenshots",
        },
        "azure": {"speech_key": "test_key", "speech_region": "test_region"},
        "transcription": {"output_format": "txt", "language": "en-US"},
    }

    config_path = tmp_path / "test_config.yaml"
    with open(config_path, "w") as f:
        yaml.dump(config_data, f)

    return config_path


def test_config_load(temp_config_file: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """Test that configuration loads correctly."""
    # Clear any existing environment variables
    monkeypatch.delenv("AZURE_SPEECH_KEY", raising=False)
    monkeypatch.delenv("AZURE_SPEECH_REGION", raising=False)

    config = Config(str(temp_config_file))
    assert config.get_path("logs") == "test_logs"
    assert config.get_azure_credentials() == {
        "speech_key": "test_key",
        "speech_region": "test_region",
    }


def test_config_env_override(
    temp_config_file: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Test that environment variables override config file values."""
    monkeypatch.setenv("AZURE_SPEECH_KEY", "env_test_key")
    monkeypatch.setenv("AZURE_SPEECH_REGION", "env_test_region")

    config = Config(str(temp_config_file))
    credentials = config.get_azure_credentials()
    assert credentials["speech_key"] == "env_test_key"
    assert credentials["speech_region"] == "env_test_region"


def test_missing_config_file() -> None:
    """Test handling of missing config file."""
    with pytest.raises(FileNotFoundError):
        Config("nonexistent_config.yaml")


def test_invalid_path_name(temp_config_file: Path) -> None:
    """Test handling of invalid path name."""
    config = Config(str(temp_config_file))
    with pytest.raises(KeyError):
        config.get_path("invalid_path")


def test_directory_creation(temp_config_file: Path) -> None:
    """Test that directories are created if they don't exist."""
    config = Config(str(temp_config_file))

    # Get paths and ensure they exist
    for path_name in ["logs", "meetings", "screenshots"]:
        path = config.get_path(path_name)
        assert os.path.exists(path)

        # Clean up
        if os.path.exists(path):
            shutil.rmtree(path)
