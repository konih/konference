import argparse
from dotenv import load_dotenv
import os
from src.speech_transcriber import SpeechTranscriber
from src.protocol_writer import ProtocolWriter
from src.config import Config
from datetime import datetime


def validate_azure_credentials(config: Config) -> None:
    """Validate that required Azure credentials are present."""
    credentials = config.get_azure_credentials()
    missing = [k for k, v in credentials.items() if not v]

    if missing:
        raise ValueError(
            f"Missing required Azure credentials: {', '.join(missing)}.\n"
            "Please ensure these are set in your config.yaml file or environment variables."
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

        # Validate Azure credentials before proceeding
        validate_azure_credentials(config)

        # Generate default output path if not specified
        if not args.output:
            meetings_dir = config.get_path("meetings")
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            extension = config.get_transcription_settings()["output_format"]
            args.output = os.path.join(meetings_dir, f"meeting_{timestamp}.{extension}")

        transcriber = SpeechTranscriber(config)
        protocol_writer = ProtocolWriter(args.output)

        protocol_writer.start_protocol()
        print(f"Starting transcription... Output will be saved to: {args.output}")
        print("Press Ctrl+C to stop")

        for transcribed_text in transcriber.start_transcription():
            protocol_writer.write_entry(transcribed_text)
            print(f"Transcribed: {transcribed_text}")

    except ValueError as e:
        print(f"Configuration Error: {str(e)}")
        return 1
    except KeyboardInterrupt:
        print("\nStopping transcription...")
    except Exception as e:
        print(f"An error occurred: {str(e)}")
        return 1
    finally:
        if "protocol_writer" in locals():
            protocol_writer.close_protocol()

    return 0


if __name__ == "__main__":
    exit(main())
