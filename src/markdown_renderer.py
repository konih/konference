from src.meeting_note import MeetingNote


class MarkdownRenderer:
    """Renders meeting notes in Markdown format."""

    @staticmethod
    def render(meeting: MeetingNote) -> str:
        """Convert a meeting note to Markdown format."""
        try:
            md_parts = [
                f"# {meeting.title}",
                "",
                "---",
                "## 👨‍👩‍👦 Attendees",
                f"{', '.join(meeting.participants)}",
                "",
                "---",
                "## 🎯 Goals",
                "1. *No goals set*",
                "",
                "## 📝 Discussion Notes",
                "- " + "\n- ".join(meeting.content)
                if meeting.content
                else "- *No notes taken*",
                "",
                "## 💠 Action Items",
                "- [ ] *No action items set*",
                "",
                "---",
                "",
                "## Meeting Details",
                f"- Date: {meeting.start_time.strftime('%Y-%m-%d %H:%M')}",
                f"- Duration: {meeting.duration}"
                if meeting.duration
                else "- Duration: Ongoing",
                f"- Tags: {', '.join(meeting.tags)}",
                "",
                "## Summary",
                meeting.summary if meeting.summary else "*No summary available*",
                "",
                "## Transcript",
                "```",
                meeting.raw_text if meeting.raw_text else "*No transcript available*",
                "```",
                "",
                "## Metadata",
                *[f"- {key}: {value}" for key, value in meeting.metadata.items()],
            ]

            return "\n".join(md_parts)
        except Exception as e:
            return f"Error rendering markdown: {str(e)}"

    @staticmethod
    def save_markdown(meeting: MeetingNote, directory: str = "meetings") -> None:
        """Save the meeting note as a Markdown file."""
        if not meeting.file_path:
            timestamp = meeting.start_time.strftime("%Y%m%d_%H%M%S")
            safe_title = "".join(c if c.isalnum() else "_" for c in meeting.title)
            md_path = f"{directory}/{timestamp}_{safe_title}.md"
        else:
            md_path = meeting.file_path.replace(".json", ".md")

        with open(md_path, "w", encoding="utf-8") as f:
            f.write(MarkdownRenderer.render(meeting))
