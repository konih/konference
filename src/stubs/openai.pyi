from typing import Any, Dict, List, Optional

from typing_extensions import TypedDict

class ChatCompletionMessageParam(TypedDict):
    role: str
    content: str

class ChatCompletionMessage(TypedDict):
    role: str
    content: str

class ChatCompletionChoice(TypedDict):
    index: int
    message: ChatCompletionMessage
    finish_reason: str

class ChatCompletion(TypedDict):
    id: str
    object: str
    created: int
    model: str
    choices: List[ChatCompletionChoice]
    usage: Dict[str, int]
    system_fingerprint: Optional[str]

class ChatCompletions:
    @staticmethod
    async def create(
        model: str,
        messages: List[ChatCompletionMessageParam],
        temperature: float = 1.0,
        max_tokens: int = 2048,
        **kwargs: Any,
    ) -> ChatCompletion: ...

class Chat:
    completions: ChatCompletions

class AsyncOpenAI:
    def __init__(self, api_key: str) -> None: ...
    chat: Chat
