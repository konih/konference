import argparse

from dotenv import load_dotenv

from src.config import Config
from src.ui.app import TranscriberUI


def validate_azure_credentials(config: Config) -> None:
    """Validate that required Azure credentials are present."""
    credentials = config.get_azure_credentials()
    missing = [k for k, v in credentials.items() if not v]

    if missing:
        raise ValueError(
            f"Missing required Azure credentials: {', '.join(missing)}.\n"
            "Please ensure these are set in your config.yaml file or environment variables."
        )


def validate_openai_credentials(config: Config) -> None:
    """Validate that required OpenAI credentials are present."""
    credentials = config.get_openai_settings()
    if not credentials["api_key"]:
        raise ValueError(
            "Missing OpenAI API key. Please set OPENAI_API_KEY environment variable."
        )


def parse_arguments() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Meeting transcription and protocol generation"
    )
    parser.add_argument(
        "--output",
        "-o",
        help="Output file path for the meeting protocol (default: auto-generated in meetings directory)",
    )
    parser.add_argument(
        "--config",
        "-c",
        default="config.yaml",
        help="Path to config file (default: config.yaml)",
    )
    return parser.parse_args()


def create_sample_meeting(app: TranscriberUI) -> None:
    """Create a sample meeting with test content for development."""
    meeting = app.meeting_store.create_meeting(
        title="Team Standup",
        participants=["Alice", "Bob", "Charlie"],
        tags=["standup", "development"],
    )

    # Add sample dialogue
    sample_content = [
        "Alice: Good morning everyone! Let's go through our updates.",
        "Bob: I've completed the authentication module yesterday. All tests are passing.",
        "Charlie: Great work Bob! I'm still working on the database optimization task.",
        "Alice: Any blockers we should discuss?",
        "Bob: Actually yes, I need some clarification on the new API requirements.",
        "Charlie: I can help with that. Let's schedule a quick call after this.",
        "Alice: Perfect. I'll update the sprint board with our progress.",
        "Bob: Also, don't forget we have the client demo tomorrow at 2 PM.",
        "Charlie: I'll prepare the presentation slides today.",
        "Alice: Excellent! Let's wrap up then. Great progress everyone!",
    ]

    # Add each line with a timestamp
    from datetime import datetime, timedelta

    base_time = datetime.now() - timedelta(minutes=30)

    for i, line in enumerate(sample_content):
        timestamp = base_time + timedelta(minutes=i * 2)
        app.meeting_store.add_content(f"[{timestamp.strftime('%H:%M:%S')}] {line}")

    meeting.save()


def main() -> int:
    # Load environment variables
    load_dotenv()

    try:
        # Parse command line arguments
        args = parse_arguments()

        # Load configuration
        config = Config(args.config)

        # Validate credentials before proceeding
        validate_azure_credentials(config)
        validate_openai_credentials(config)

        # Get user settings
        user_settings = config.get_user_settings()

        # Create and run the UI with default participant
        app = TranscriberUI(default_participant=user_settings["default_participant"])

        # Create sample meeting for testing if configured
        if user_settings["create_default_meeting"]:
            create_sample_meeting(app)

        app.run()

    except ValueError as e:
        print(f"Configuration Error: {str(e)}")
        return 1
    except KeyboardInterrupt:
        print("\nStopping transcription...")
    except Exception as e:
        print(f"An error occurred: {str(e)}")
        return 1

    return 0


if __name__ == "__main__":
    exit(main())
