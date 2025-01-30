# Konference

An automated meeting minutes generator that uses Azure Speech Services to transcribe audio in real-time, capture screenshots, and generate formatted markdown summaries.

## Features

- 🎤 Real-time audio transcription using Azure Speech Services
- 📸 Screenshot capture functionality
- 📝 Automatic meeting summary generation in Markdown format
- 🕒 Meeting start/end time tracking
- 🖼️ Screenshot organization and embedding in summaries
- 🎯 Background process for continuous transcription

## Prerequisites

- Python 3.11 or higher
- Azure Speech Services subscription
- Linux or macOS (Windows support coming soon)
- Task (taskfile) installed

## Quick Start

1. Clone the repository:
```bash
git clone https://github.com/yourusername/meeting-minutes-transcriber.git
cd meeting-minutes-transcriber
```

2. Run the full setup:
```bash
task full-setup
```

3. Update your Azure credentials in the `.env` file:
```env
AZURE_SPEECH_KEY=your_key_here
AZURE_SPEECH_REGION=your_region_here
```

4. Start a meeting:
```bash
task start-meeting
```

5. Take screenshots during the meeting:
```bash
task screenshot
```

6. End the meeting and generate summary:
```bash
task end-meeting
```

## Usage

### Starting a Meeting
```bash
task start-meeting
```
This will:
- Start audio transcription in the background
- Create a new meeting session
- Begin logging timestamps

### Taking Screenshots
```bash
task screenshot
```
Captures the current screen and saves it to the meeting record.

### Ending a Meeting
```bash
task end-meeting
```
This will:
- Stop the transcription
- Generate a markdown summary
- Include all screenshots
- Save everything to the `meetings/` directory

## Directory Structure

```
meeting-minutes-transcriber/
├── src/
│   ├── audio_capture.py
│   ├── speech_transcriber.py
│   ├── screenshot.py
│   ├── meeting_manager.py
│   └── main.py
├── tests/
├── meetings/
├── screenshots/
├── requirements.txt
└── .env
```

## Generated Summary Format

The generated meeting summary will include:

- Meeting date and time
- Duration
- Participants (if available)
- Full transcript with timestamps
- Screenshots with timestamps
- Key points (AI-generated)
- Action items (AI-extracted)

## Development

- Run tests: `task test`
- Run linting: `task lint`
- Clean project: `task clean`

## Contributing

1. Fork the repository
2. Create your feature branch
3. Commit your changes
4. Push to the branch
5. Create a Pull Request

## License

MIT

## Acknowledgments

- Azure Speech Services
- Python Speech SDK
- PyAudio
