import os
from typing import Dict, TypedDict, cast, Literal, Any

import yaml  # We don't need the type ignore comment anymore since we configured it in mypy.ini


class AzureConfig(TypedDict):
    speech_key: str
    speech_region: str


class TranscriptionConfig(TypedDict):
    output_format: str
    language: str
    enable_timestamps: bool


class PathsConfig(TypedDict):
    logs: str
    meetings: str
    screenshots: str


class LoggingConfig(TypedDict):
    level: str
    file_logging_enabled: bool


class UserConfig(TypedDict):
    default_participant: str
    create_default_meeting: bool


class AudioConfig(TypedDict):
    enabled: bool
    format: int  # pyaudio format
    channels: int
    rate: int
    chunk: int


class OpenAIConfig(TypedDict):
    model: str
    temperature: float
    max_tokens: int


class AppConfig(TypedDict):
    paths: PathsConfig
    azure: AzureConfig
    transcription: TranscriptionConfig
    logging: LoggingConfig
    user: UserConfig
    audio: AudioConfig
    openai: OpenAIConfig  # Add OpenAI config


PathName = Literal["logs", "meetings", "screenshots"]


class Config:
    """Configuration manager for the application."""

    def __init__(self, config_file: str = "config.yaml") -> None:
        """Initialize configuration from file and environment variables."""
        self.config_file = config_file
        self.config = self._load_config()
        self._create_directories()

    def _load_config(self) -> AppConfig:
        """Load configuration from file."""
        if not os.path.exists(self.config_file):
            raise FileNotFoundError(f"Config file not found: {self.config_file}")

        with open(self.config_file, "r") as f:
            config_data = yaml.safe_load(f)
            return cast(AppConfig, config_data)

    def _create_directories(self) -> None:
        """Create necessary directories if they don't exist."""
        for path_name in ["logs", "meetings", "screenshots"]:
            path = self.get_path(cast(PathName, path_name))
            os.makedirs(path, exist_ok=True)

    def get_path(self, name: PathName) -> str:
        """Get path from configuration."""
        if name not in self.config["paths"]:
            raise KeyError(f"Path not found in config: {name}")
        return self.config["paths"][
            name
        ]  # Removed redundant cast since we know it's a str from PathsConfig

    def get_azure_credentials(self) -> Dict[str, str]:
        """Get Azure credentials, with environment variables taking precedence."""
        return {
            "speech_key": os.getenv(
                "AZURE_SPEECH_KEY", self.config["azure"]["speech_key"]
            ),
            "speech_region": os.getenv(
                "AZURE_SPEECH_REGION", self.config["azure"]["speech_region"]
            ),
        }

    def get_transcription_settings(self) -> TranscriptionConfig:
        """Get transcription settings."""
        return cast(TranscriptionConfig, self.config["transcription"])

    def get_logging_settings(self) -> LoggingConfig:
        """Get logging settings."""
        return cast(LoggingConfig, self.config["logging"])

    def get_user_settings(self) -> UserConfig:
        """Get user settings."""
        return cast(
            UserConfig,
            self.config.get(
                "user", {"default_participant": "", "create_default_meeting": False}
            ),
        )

    def get_speech_config(self) -> Dict[str, str]:
        """Get speech configuration settings."""
        # Default implementation - override or extend as needed
        return {"subscription": "", "region": ""}

    def get_openai_settings(self) -> Dict[str, Any]:
        """Get OpenAI settings, with environment variables taking precedence."""
        return {
            "api_key": os.getenv("OPENAI_API_KEY", ""),
            "model": self.config["openai"]["model"],
            "temperature": self.config["openai"]["temperature"],
            "max_tokens": self.config["openai"]["max_tokens"],
        }

    def get_system_prompt(self) -> str:
        """Get the system prompt for OpenAI."""
        return """You are an expert meeting summarizer. Your task is to analyze meeting transcripts and create clear, concise summaries that capture the essential information. Focus on:

1. Key Discussion Points
- Main topics covered
- Important decisions made
- Problems discussed and solutions proposed

2. Action Items
- Tasks assigned
- Deadlines mentioned
- Responsibilities delegated

3. Follow-up Items
- Items requiring further discussion
- Scheduled follow-up meetings
- Outstanding questions

Format the summary in a professional, easy-to-read structure using markdown. Be concise but comprehensive, ensuring no critical information is lost. Maintain a neutral, professional tone.

The transcript will be provided in chronological order with timestamps. Focus on synthesizing the content rather than preserving every detail.

Current meeting context:
Title: {title}
Date: {date}
Duration: {duration}
Participants: {participants}

Transcript follows:
"""
