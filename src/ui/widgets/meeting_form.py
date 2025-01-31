from typing import List, Optional, Tuple

from textual.app import ComposeResult
from textual.containers import Container, Horizontal, Vertical
from textual.message import Message
from textual.widgets import Static, Input, TextArea, Button


class FormResult(Message):
    """Message sent when form is submitted or cancelled."""

    def __init__(self, result: Optional[Tuple[str, List[str], List[str]]]) -> None:
        self.result = result
        super().__init__()


class MeetingForm(Static):
    """Form for editing meeting details."""

    DEFAULT_CSS = """
    MeetingForm {
        layout: vertical;
        height: 100%;
        width: 100%;
        background: $surface;
        padding: 1;
        overflow-y: auto;  # Allow scrolling if content is too long
    }

    .form-container {
        height: auto;
        width: 100%;
        margin: 1;
        align: center top;  # Align to top
    }

    .field-label {
        padding: 1 0;
        text-style: bold;
        color: $text;
        width: 100%;
    }

    .field-hint {
        color: $text-muted;
        text-style: italic;
        width: 100%;
    }

    Input {
        width: 100%;
        margin: 1 0;
        border: solid $primary;
        height: 3;
        background: $surface-lighten-2;
        color: $text;
        padding: 0 1;
    }

    Input:focus {
        background: $surface-lighten-3;
        border: double $accent;
    }

    TextArea {
        width: 100%;
        height: 8;
        margin: 1 0;
        border: solid $primary;
        background: $surface-lighten-2;
        color: $text;
        padding: 1;
    }

    TextArea:focus {
        background: $surface-lighten-3;
        border: double $accent;
    }

    #button-container {
        width: 100%;
        height: auto;
        align: center middle;
        padding: 1;
        margin-top: 1;
    }

    Button {
        margin: 1 2;
        min-width: 16;
        height: 3;
    }

    #save {
        background: $success;
    }

    #cancel {
        background: $error;
    }
    """

    def __init__(
        self,
        title: str = "",
        participants: Optional[List[str]] = None,
        tags: Optional[List[str]] = None,
    ) -> None:
        super().__init__()
        self.meeting_title = title
        self.meeting_participants = participants or []
        self.meeting_tags = tags or []

    def compose(self) -> ComposeResult:
        """Create child widgets for the form."""
        with Vertical(classes="form-container"):
            yield Static("Meeting Title:", classes="field-label")
            yield Input(
                value=self.meeting_title, id="title", placeholder="Enter meeting title"
            )

            yield Static("Participants:", classes="field-label")
            yield Static("(one name per line)", classes="field-hint")
            yield TextArea("\n".join(self.meeting_participants), id="participants")

            yield Static("Tags:", classes="field-label")
            yield Static("(one tag per line)", classes="field-hint")
            yield TextArea("\n".join(self.meeting_tags), id="tags")

            with Container(id="button-container"):
                with Horizontal():
                    yield Button("💾 Save", variant="success", id="save")
                    yield Button("❌ Cancel", variant="error", id="cancel")

    def on_mount(self) -> None:
        """Handle form mounting."""
        self.focus()  # Focus the form when mounted

    async def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle button press events."""
        if event.button.id == "save":
            result = self.collect_form_data()
            await self.post_message(FormResult(result))
        elif event.button.id == "cancel":
            await self.post_message(FormResult(None))

    def collect_form_data(self) -> Tuple[str, List[str], List[str]]:
        """Collect and validate form data."""
        title = self.query_one("#title", Input).value.strip()
        participants_text = self.query_one("#participants", TextArea).text
        tags_text = self.query_one("#tags", TextArea).text

        participants = [p.strip() for p in participants_text.splitlines() if p.strip()]
        tags = [t.strip() for t in tags_text.splitlines() if t.strip()]

        return (title, participants, tags)
