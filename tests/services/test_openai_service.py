from unittest.mock import Mock, AsyncMock

import pytest

from src.services.openai_service import OpenAIService


@pytest.mark.asyncio
async def test_generate_summary(monkeypatch: pytest.MonkeyPatch) -> None:
    """Test summary generation."""
    # Mock config
    mock_config = Mock()
    mock_config.get_openai_settings.return_value = {
        "api_key": "test_key",
        "model": "gpt-4",
        "temperature": 0.7,
        "max_tokens": 1000,
    }
    mock_config.get_system_prompt.return_value = "Test prompt {title}"

    # Mock OpenAI client
    mock_client = Mock()
    mock_client.chat.completions.create = AsyncMock(
        return_value=Mock(choices=[Mock(message=Mock(content="Test summary"))])
    )

    # Mock AsyncOpenAI constructor
    mock_openai = Mock()
    mock_openai.return_value = mock_client
    monkeypatch.setattr("openai.AsyncOpenAI", mock_openai)

    # Test successful generation
    service = OpenAIService(mock_config)
    result = await service.generate_summary({"title": "Test"})
    assert result == "Test summary"

    # Test error handling
    mock_client.chat.completions.create.side_effect = Exception("API Error")
    with pytest.raises(RuntimeError, match="Error generating summary"):
        await service.generate_summary({"title": "Test"})
