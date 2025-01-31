from typing import Dict, Any, TypedDict, List
from openai.types.chat import ChatCompletionMessageParam
from src.config import Config


class ChatMessage(TypedDict):
    role: str
    content: str


class OpenAIService:
    """Service for interacting with OpenAI API."""

    def __init__(self, config: Config) -> None:
        """Initialize OpenAI service with configuration."""
        try:
            from openai import AsyncOpenAI

            settings = config.get_openai_settings()
            self.client = AsyncOpenAI(api_key=settings["api_key"])
            self.model = settings["model"]
            self.temperature = settings["temperature"]
            self.max_tokens = settings["max_tokens"]
            self.system_prompt = config.get_system_prompt()
        except ImportError:
            raise RuntimeError(
                "OpenAI package not installed. Please install 'openai>=1.0.0'"
            )

    async def generate_summary(self, meeting_data: Dict[str, Any]) -> str:
        """Generate a meeting summary using OpenAI."""
        try:
            formatted_prompt = self.system_prompt.format(
                title=meeting_data.get("title", "Untitled Meeting"),
                date=meeting_data.get("date", ""),
                duration=meeting_data.get("duration", ""),
                participants=", ".join(meeting_data.get("participants", [])),
            )

            messages: List[ChatCompletionMessageParam] = [
                {"role": "system", "content": formatted_prompt},
                {"role": "user", "content": meeting_data.get("content", "")},
            ]

            response = await self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                temperature=self.temperature,
                max_tokens=self.max_tokens,
            )

            content = response.choices[0].message.content
            if content is None:
                raise RuntimeError("Received empty response from OpenAI")

            return str(content)

        except Exception as e:
            raise RuntimeError(f"Error generating summary: {str(e)}")
