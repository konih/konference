import argparse
from dotenv import load_dotenv
import os
from src.speech_transcriber import SpeechTranscriber
from src.protocol_writer import ProtocolWriter


def validate_azure_credentials() -> None:
    """Validate that required Azure credentials are present."""
    required_vars = ["AZURE_SPEECH_KEY", "AZURE_SPEECH_REGION"]
    missing = [var for var in required_vars if not os.getenv(var)]

    if missing:
        raise ValueError(
            f"Missing required Azure credentials: {', '.join(missing)}.\n"
            "Please ensure these are set in your .env file."
        )


def parse_arguments() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Meeting transcription and protocol generation"
    )
    parser.add_argument(
        "--output",
        "-o",
        default="meeting_protocol.txt",
        help="Output file path for the meeting protocol (default: meeting_protocol.txt)",
    )
    return parser.parse_args()


def main() -> int:
    # Load environment variables
    load_dotenv()

    try:
        # Validate Azure credentials before proceeding
        validate_azure_credentials()

        # Parse command line arguments
        args = parse_arguments()

        transcriber = SpeechTranscriber()
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
