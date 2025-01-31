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
        app = TranscriberUI(
            default_participant=user_settings["default_participant"],
            create_sample=user_settings["create_default_meeting"],
        )

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
