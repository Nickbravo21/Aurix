"""
OpenAI integration for AI-powered analysis.
"""
import json
from typing import Any

import openai
from tenacity import (
    retry,
    stop_after_attempt,
    wait_exponential,
    retry_if_exception_type,
)

from ..core.config import settings
from ..core.logging import get_logger

logger = get_logger(__name__)

# Configure OpenAI client
client = openai.AsyncOpenAI(api_key=settings.openai_api_key)


class RateLimitError(Exception):
    """Raised when API rate limit is exceeded."""
    pass


@retry(
    retry=retry_if_exception_type((openai.RateLimitError, openai.APITimeoutError)),
    stop=stop_after_attempt(settings.ai_retry_attempts),
    wait=wait_exponential(multiplier=1, min=2, max=10),
)
async def call_gpt(
    messages: list[dict[str, str]],
    model: str | None = None,
    temperature: float | None = None,
    max_tokens: int | None = None,
    response_format: dict[str, str] | None = None,
) -> str:
    """
    Call OpenAI GPT API with retry logic.
    
    Args:
        messages: List of message dicts with role and content
        model: Model name (defaults to settings)
        temperature: Sampling temperature (defaults to settings)
        max_tokens: Max tokens in response (defaults to settings)
        response_format: Response format spec (e.g., {"type": "json_object"})
    
    Returns:
        Response content string
    
    Raises:
        RateLimitError: If rate limit exceeded after retries
        ValueError: If API returns error
    """
    try:
        response = await client.chat.completions.create(
            model=model or settings.openai_model,
            messages=messages,
            temperature=temperature if temperature is not None else settings.openai_temperature,
            max_tokens=max_tokens or settings.openai_max_tokens,
            response_format=response_format,
            timeout=settings.ai_timeout_seconds,
        )
        
        content = response.choices[0].message.content
        
        if not content:
            raise ValueError("Empty response from OpenAI")
        
        # Log usage
        if hasattr(response, "usage"):
            logger.debug(
                f"OpenAI usage: {response.usage.prompt_tokens} prompt + "
                f"{response.usage.completion_tokens} completion = "
                f"{response.usage.total_tokens} total tokens"
            )
        
        return content
        
    except openai.RateLimitError as e:
        logger.warning(f"OpenAI rate limit hit: {e}")
        raise RateLimitError("API rate limit exceeded") from e
    
    except openai.APITimeoutError as e:
        logger.warning(f"OpenAI timeout: {e}")
        raise
    
    except openai.APIError as e:
        logger.error(f"OpenAI API error: {e}")
        raise ValueError(f"OpenAI API error: {e}") from e


async def generate_json_response(
    system_prompt: str,
    user_content: dict[str, Any] | str,
    model: str | None = None,
) -> dict[str, Any]:
    """
    Generate structured JSON response from AI.
    
    Args:
        system_prompt: System prompt defining task
        user_content: User message (dict will be JSON serialized)
        model: Optional model override
    
    Returns:
        Parsed JSON response
    """
    if isinstance(user_content, dict):
        user_content = json.dumps(user_content, indent=2)
    
    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_content},
    ]
    
    response = await call_gpt(
        messages=messages,
        model=model,
        response_format={"type": "json_object"},
    )
    
    try:
        return json.loads(response)
    except json.JSONDecodeError as e:
        logger.error(f"Failed to parse JSON response: {response}")
        raise ValueError("AI returned invalid JSON") from e


async def generate_text_response(
    system_prompt: str,
    user_content: str,
    model: str | None = None,
) -> str:
    """
    Generate plain text response from AI.
    
    Args:
        system_prompt: System prompt
        user_content: User message
        model: Optional model override
    
    Returns:
        Response text
    """
    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_content},
    ]
    
    return await call_gpt(messages=messages, model=model)


async def stream_response(
    messages: list[dict[str, str]],
    model: str | None = None,
):
    """
    Stream GPT response for real-time display.
    
    Args:
        messages: Conversation messages
        model: Model name
    
    Yields:
        Response chunks
    """
    try:
        stream = await client.chat.completions.create(
            model=model or settings.openai_model,
            messages=messages,
            temperature=settings.openai_temperature,
            max_tokens=settings.openai_max_tokens,
            stream=True,
        )
        
        async for chunk in stream:
            if chunk.choices[0].delta.content:
                yield chunk.choices[0].delta.content
                
    except Exception as e:
        logger.error(f"Error streaming response: {e}")
        raise
