import pytest
from src.main import validate_azure_credentials, parse_arguments
from src.config import Config
from unittest.mock import MagicMock, patch
import sys


def test_validate_azure_credentials_valid() -> None:
    """Test validation with valid credentials."""
    mock_config = MagicMock(spec=Config)
    mock_config.get_azure_credentials.return_value = {
        "speech_key": "test_key",
        "speech_region": "test_region",
    }

    # Should not raise an exception
    validate_azure_credentials(mock_config)


def test_validate_azure_credentials_invalid() -> None:
    """Test validation with missing credentials."""
    mock_config = MagicMock(spec=Config)
    mock_config.get_azure_credentials.return_value = {
        "speech_key": "",
        "speech_region": "test_region",
    }

    with pytest.raises(ValueError) as exc:
        validate_azure_credentials(mock_config)
    assert "speech_key" in str(exc.value)


def test_parse_arguments_defaults() -> None:
    """Test argument parsing with defaults."""
    with patch.object(sys, "argv", ["prog"]):
        args = parse_arguments()
        assert args.output is None
        assert args.config == "config.yaml"


def test_parse_arguments_custom() -> None:
    """Test argument parsing with custom values."""
    test_args = [
        "prog",
        "--output",
        "custom_output.txt",
        "--config",
        "custom_config.yaml",
    ]
    with patch.object(sys, "argv", test_args):
        args = parse_arguments()
        assert args.output == "custom_output.txt"
        assert args.config == "custom_config.yaml"
