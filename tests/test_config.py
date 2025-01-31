import os
import shutil
from pathlib import Path

import pytest
import yaml
from pytest import FixtureRequest

from src.config import Config, PathName


@pytest.fixture(scope="function")
def temp_config_file(request: FixtureRequest, tmp_path: Path) -> Path:
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
        # Use an invalid path name that's not in the PathName Literal type
        config.get_path("invalid_path")  # type: ignore


def test_directory_creation(temp_config_file: Path) -> None:
    """Test that directories are created if they don't exist."""
    config = Config(str(temp_config_file))

    # Get paths and ensure they exist
    paths: list[PathName] = ["logs", "meetings", "screenshots"]
    for path_name in paths:
        path = config.get_path(path_name)
        assert os.path.exists(path)

        # Clean up
        if os.path.exists(path):
            shutil.rmtree(path)


def test_user_settings(temp_config_file: Path) -> None:
    """Test user settings configuration."""
    config_data = {
        "paths": {
            "logs": "test_logs",
            "meetings": "test_meetings",
            "screenshots": "test_screenshots",
        },
        "azure": {"speech_key": "test_key", "speech_region": "test_region"},
        "transcription": {"output_format": "txt", "language": "en-US"},
        "user": {"default_participant": "Test User", "create_default_meeting": True},
    }

    with open(temp_config_file, "w") as f:
        yaml.dump(config_data, f)

    config = Config(str(temp_config_file))
    user_settings = config.get_user_settings()

    assert user_settings["default_participant"] == "Test User"
    assert user_settings["create_default_meeting"] is True


def test_default_user_settings(temp_config_file: Path) -> None:
    """Test default user settings when not specified in config."""
    config_data = {
        "paths": {
            "logs": "test_logs",
            "meetings": "test_meetings",
            "screenshots": "test_screenshots",
        }
    }

    with open(temp_config_file, "w") as f:
        yaml.dump(config_data, f)

    config = Config(str(temp_config_file))
    user_settings = config.get_user_settings()

    assert user_settings["default_participant"] == ""
    assert user_settings["create_default_meeting"] is False
