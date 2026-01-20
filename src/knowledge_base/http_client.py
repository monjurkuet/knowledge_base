"""
Shared HTTP client for OpenAI-compatible API calls
"""

import asyncio
import json
import logging
from typing import Any, cast

import httpx

from knowledge_base.config import get_config

logger = logging.getLogger(__name__)


class ChatMessage:
    """Chat message model matching OpenAI API"""

    def __init__(
        self,
        role: str,
        content: str | None = None,
        tool_calls: list[dict[str, Any]] | None = None,
        tool_call_id: str | None = None,
    ):
        self.role = role
        self.content = content
        self.tool_calls = tool_calls
        self.tool_call_id = tool_call_id

    def to_dict(self) -> dict[str, Any]:
        """Convert to dict for JSON serialization"""
        result: dict[str, Any] = {"role": self.role}
        if self.content is not None:
            result["content"] = self.content
        if self.tool_calls is not None:
            result["tool_calls"] = self.tool_calls
        if self.tool_call_id is not None:
            result["tool_call_id"] = self.tool_call_id
        return result


class ChatCompletionRequest:
    """Chat completion request model matching OpenAI API"""

    def __init__(
        self,
        model: str,
        messages: list[ChatMessage],
        tools: list[dict[str, Any]] | None = None,
        tool_choice: Any | None = "auto",
        temperature: float = 0.7,
        max_tokens: int = 2000,
        stream: bool = False,
    ):
        self.model = model
        self.messages = messages
        self.tools = tools
        self.tool_choice = tool_choice
        self.temperature = temperature
        self.max_tokens = max_tokens
        self.stream = stream

    def to_dict(self) -> dict[str, Any]:
        """Convert to dict for JSON serialization"""
        result = {
            "model": self.model,
            "messages": [msg.to_dict() for msg in self.messages],
            "temperature": self.temperature,
            "max_tokens": self.max_tokens,
        }
        if self.tools is not None:
            result["tools"] = self.tools
        if self.tool_choice is not None:
            result["tool_choice"] = self.tool_choice
        if self.stream:
            result["stream"] = True
        return result


class HTTPClient:
    """
    HTTP client for OpenAI-compatible API calls following reference implementation pattern
    """

    MAX_RETRIES = 2
    RETRY_DELAY = 3.0
    TIMEOUT_SECONDS = 30

    def __init__(self, base_url: str | None = None, api_key: str | None = None):
        config = get_config()
        self.api_url = (base_url or config.llm.openai_api_base).rstrip("/")
        self.api_key = api_key or config.llm.api_key
        self.timeout = httpx.Timeout(self.TIMEOUT_SECONDS)

    async def chat_completion(
        self, request: ChatCompletionRequest, stream: bool = False
    ) -> dict[str, Any] | None:
        """
        Send chat completion request to API

        Args:
            request: ChatCompletionRequest object
            stream: Whether to stream the response

        Returns:
            Response JSON dict or None if failed
        """
        url = f"{self.api_url}/chat/completions"
        headers = {"Content-Type": "application/json"}

        for attempt in range(self.MAX_RETRIES):
            try:
                async with httpx.AsyncClient(timeout=self.timeout) as client:
                    if stream:
                        return await self._stream_response(
                            client, url, headers, request
                        )
                    else:
                        response = await client.post(
                            url,
                            headers=headers,
                            json=request.to_dict(),
                        )
                        response.raise_for_status()
                        result = response.json()
                        return cast(dict[str, Any], result)
            except httpx.TimeoutException:
                logger.warning(f"Timeout attempt {attempt + 1}/{self.MAX_RETRIES}")
                if attempt < self.MAX_RETRIES - 1:
                    await asyncio.sleep(self.RETRY_DELAY * (2**attempt))
            except Exception as e:
                error_msg = str(e)
                logger.error(f"Request failed: {error_msg}")
                if (
                    "model_not_supported" in error_msg.lower()
                    or "The requested model is not supported" in error_msg
                ):
                    return {"error": {"message": "Model not supported"}}
                if attempt < self.MAX_RETRIES - 1:
                    await asyncio.sleep(self.RETRY_DELAY * (2**attempt))
                else:
                    raise
        return None

    async def _stream_response(
        self,
        client: httpx.AsyncClient,
        url: str,
        headers: dict[str, str],
        request: ChatCompletionRequest,
    ) -> dict[str, Any] | None:
        """Handle streaming response"""
        async with client.stream(
            "POST", url, headers=headers, json=request.to_dict()
        ) as response:
            response.raise_for_status()
            chunks = []
            async for line in response.aiter_lines():
                if line.startswith("data: "):
                    data = line[6:]
                    if data == "[DONE]":
                        break
                    try:
                        chunk = json.loads(data)
                        chunks.append(chunk)
                    except json.JSONDecodeError:
                        continue
            return {"chunks": chunks}
