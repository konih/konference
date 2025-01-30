# Konference

An automated meeting minutes generator that uses Azure Speech Services to transcribe audio in real-time, with a beautiful terminal UI for managing recordings, capturing screenshots, and generating formatted markdown summaries.

## Features

- 🎤 Real-time audio transcription using Azure Speech Services
- 🖥️ Beautiful terminal UI with:
  - Live transcription stream
  - Recording timer
  - Status indicators
  - Quick action buttons
- 📸 Screenshot capture functionality
- 📝 Automatic meeting summary generation in Markdown format
- 🕒 Meeting start/end time tracking
- 🖼️ Screenshot organization and embedding in summaries
- 🎯 Background process for continuous transcription
- ⌨️ Keyboard shortcuts for quick actions

## Prerequisites

- Python 3.11 or higher
- Azure Speech Services subscription
- Linux or macOS (Windows support coming soon)
- Task (taskfile) installed
- PortAudio (for audio capture)

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

4. Start Konference:
```bash
task run-konference
```

## Terminal UI Controls

### Keyboard Shortcuts
- `Space`: Start/Stop recording
- `S`: Take screenshot
- `M`: Generate meeting summary
- `Q`: Quit application

### UI Elements
- Status Bar: Shows recording state and elapsed time
- Transcript Window: Real-time transcription feed
- Action Buttons:
  - 🎙 Start/Stop: Toggle recording
  - 📸 Screenshot: Capture screen
  - ⚙️ Settings: Configure application
  - 📝 Summarize: Generate meeting summary

## Directory Structure

```
meeting-minutes-transcriber/
├── src/
│   ├── audio_capture.py      # Audio input handling
│   ├── speech_transcriber.py # Azure speech integration
│   ├── protocol_writer.py    # Transcript management
│   ├── config.py            # Configuration handling
│   ├── ui/                  # Terminal UI components
│   │   └── app.py          # Main UI application
│   └── main.py             # Application entry point
├── tests/                   # Test suite
├── meetings/               # Meeting transcripts
├── screenshots/            # Captured screenshots
├── requirements.txt        # Production dependencies
└── requirements-dev.txt    # Development dependencies
```

## Generated Summary Format

The generated meeting summary includes:

- Meeting date and time
- Duration
- Full transcript with timestamps
- Screenshots with timestamps
- Key points (AI-generated)
- Action items (AI-extracted)

Example:
```markdown
# Meeting Summary - 2024-02-15

## Details
- Start Time: 14:30:00
- End Time: 15:45:00
- Duration: 1h 15m

## Transcript
[14:30:15] Meeting started, discussing Q1 goals
[14:35:22] Team updates from engineering
...

## Screenshots
- [14:40:00] Sprint board review
- [15:15:30] Architecture diagram discussion

## Key Points
1. Q1 targets set for all teams
2. New architecture approved
...
```

## Development

### Setup Development Environment
```bash
task setup
```

### Common Tasks
- Run tests: `task test`
- Run linting: `task lint`
- Type checking: `task mypy`
- Clean project: `task clean`
- Update dependencies: `task update-deps`

### Code Style
- Black formatting
- Type hints required
- Docstrings for all public functions
- Tests required for new features

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
- Textual TUI Framework
- Rich Text Formatting
- PyAudio
