from typing import Dict, Any, TypedDict, List
# type: ignore[import]
from openai.types.chat import ChatCompletionMessageParam
from src.config import Config
from src.logger import AppLogger


class ChatMessage(TypedDict):
    role: str
    content: str


class OpenAIService:
    """Service for interacting with OpenAI API."""

    def __init__(self, config: Config) -> None:
        """Initialize OpenAI service with configuration."""
        self.logger = AppLogger().logger
        self.logger.info("Initializing OpenAI service")

        try:
            from openai import AsyncOpenAI

            settings = config.get_openai_settings()
            self.client = AsyncOpenAI(api_key=settings["api_key"])
            self.model = settings["model"]
            self.temperature = settings["temperature"]
            self.max_tokens = settings["max_tokens"]
            self.system_prompt = config.get_system_prompt()

            self.logger.debug(
                f"OpenAI service configured with model={self.model}, "
                f"temperature={self.temperature}, max_tokens={self.max_tokens}"
            )
        except ImportError:
            self.logger.error("Failed to import OpenAI package")
            raise RuntimeError(
                "OpenAI package not installed. Please install 'openai>=1.0.0'"
            )

    async def generate_summary(self, meeting_data: Dict[str, Any]) -> str:
        """Generate a meeting summary using OpenAI."""
        self.logger.info("Starting meeting summary generation")
        self.logger.debug(f"Raw meeting data: {meeting_data}")

        try:
            # Debug raw data
            title = meeting_data.get("title", "Untitled Meeting")
            participants = meeting_data.get("participants", [])
            content = meeting_data.get("content", "")

            self.logger.debug(f"Title: {title}")
            self.logger.debug(f"Participants (raw): {participants}")
            self.logger.debug(f"Content: {content[:200]}...")  # First 200 chars

            # Fix participants joining
            participants_str = (
                ", ".join(participants)
                if isinstance(participants, list)
                else str(participants)
            )
            self.logger.debug(f"Participants (formatted): {participants_str}")

            formatted_prompt = self.system_prompt.format(
                title=title,
                date=meeting_data.get("date", ""),
                duration=meeting_data.get("duration", ""),
                participants=participants_str,
            )

            self.logger.debug(f"Formatted system prompt: {formatted_prompt}")

            messages: List[ChatCompletionMessageParam] = [
                {"role": "system", "content": formatted_prompt},
                {"role": "user", "content": content},
            ]

            self.logger.debug(f"Final messages structure: {messages}")

            self.logger.info("Sending request to OpenAI API")
            response = await self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                temperature=self.temperature,
                max_tokens=self.max_tokens,
            )

            self.logger.debug(f"Raw OpenAI response: {response}")
            self.logger.debug(f"Response choices: {response.choices}")

            content = response.choices[0].message.content  # type: ignore[attr-defined]
            self.logger.debug(f"Extracted content: {content}")

            if content is None:
                self.logger.error("Received empty response from OpenAI")
                raise RuntimeError("Received empty response from OpenAI")

            self.logger.info("Successfully generated meeting summary")
            self.logger.debug(f"Summary length: {len(str(content))} characters")
            self.logger.debug(f"Final summary content: {content}")
            return str(content)

        except Exception as e:
            self.logger.error(f"Error generating summary: {str(e)}", exc_info=True)
            raise RuntimeError(f"Error generating summary: {str(e)}")
