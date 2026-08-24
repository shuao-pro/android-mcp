"""Vision model clients: Anthropic Claude, OpenAI GPT-4o, and custom endpoints."""

import json
from typing import Optional

import httpx

from android_mcp.vision.models import VisionClient, VisionResult
from android_mcp.vision.prompts import build_vision_prompt, _parse_vision_response


class AnthropicVisionClient:
    """Vision client for Anthropic Claude (Messages API)."""

    def __init__(
        self,
        api_key: str,
        model: str = "claude-sonnet-5",
        timeout: float = 30.0,
    ):
        self.api_key = api_key
        self.model = model
        self.base_url = "https://api.anthropic.com/v1/messages"
        self.timeout = timeout

    async def analyze_screenshot(
        self,
        base64_image: str,
        target_description: str,
        screen_width: int = 0,
        screen_height: int = 0,
    ) -> VisionResult:
        """Send screenshot to Claude Vision API."""
        system_prompt = build_vision_prompt(
            target_description, screen_width, screen_height
        )

        payload = {
            "model": self.model,
            "max_tokens": 1024,
            "system": system_prompt,
            "messages": [
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "image",
                            "source": {
                                "type": "base64",
                                "media_type": "image/png",
                                "data": base64_image,
                            },
                        },
                        {
                            "type": "text",
                            "text": f"Find this UI element: {target_description}",
                        },
                    ],
                }
            ],
        }

        try:
            async with httpx.AsyncClient() as client:
                resp = await client.post(
                    self.base_url,
                    json=payload,
                    headers={
                        "x-api-key": self.api_key,
                        "anthropic-version": "2023-06-01",
                        "content-type": "application/json",
                    },
                    timeout=self.timeout,
                )
                resp.raise_for_status()
                data = resp.json()

            content_blocks = data.get("content", [])
            text_parts = []
            for block in content_blocks:
                if block.get("type") == "text":
                    text_parts.append(block.get("text", ""))

            raw_text = "\n".join(text_parts).strip()
            if not raw_text:
                return VisionResult(
                    found=False,
                    raw_response=json.dumps(data),
                    error="Vision model returned empty response",
                )

            return _parse_vision_response(raw_text)

        except httpx.HTTPStatusError as e:
            return VisionResult(
                found=False,
                error=f"Vision API HTTP error {e.response.status_code}: {e.response.text[:500]}",
            )
        except httpx.TimeoutException:
            return VisionResult(
                found=False,
                error=f"Vision API request timed out after {self.timeout}s",
            )
        except Exception as e:
            return VisionResult(
                found=False,
                error=f"Vision API error: {e}",
            )

    async def chat(self, system_prompt: str, messages: list[dict]) -> str:
        """Send a plain-text chat request to the Anthropic Messages API.

        Returns the assistant's text reply (empty string if none).
        Raises on transport/HTTP errors; callers are expected to handle them.
        """
        payload = {
            "model": self.model,
            "max_tokens": 1024,
            "system": system_prompt,
            "messages": messages,
        }

        async with httpx.AsyncClient() as client:
            resp = await client.post(
                self.base_url,
                json=payload,
                headers={
                    "x-api-key": self.api_key,
                    "anthropic-version": "2023-06-01",
                    "content-type": "application/json",
                },
                timeout=self.timeout,
            )
            resp.raise_for_status()
            data = resp.json()

        text_parts = [
            block.get("text", "")
            for block in data.get("content", [])
            if block.get("type") == "text"
        ]
        return "\n".join(text_parts).strip()

    async def describe_screenshot(
        self, base64_image: str, question: str = "Describe the current screen."
    ) -> str:
        """Return a free-form text description of a screenshot (multimodal)."""
        payload = {
            "model": self.model,
            "max_tokens": 1024,
            "messages": [
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "image",
                            "source": {
                                "type": "base64",
                                "media_type": "image/png",
                                "data": base64_image,
                            },
                        },
                        {"type": "text", "text": question},
                    ],
                }
            ],
        }
        try:
            async with httpx.AsyncClient() as client:
                resp = await client.post(
                    self.base_url,
                    json=payload,
                    headers={
                        "x-api-key": self.api_key,
                        "anthropic-version": "2023-06-01",
                        "content-type": "application/json",
                    },
                    timeout=self.timeout,
                )
                resp.raise_for_status()
                data = resp.json()
            parts = [
                block.get("text", "")
                for block in data.get("content", [])
                if block.get("type") == "text"
            ]
            return "\n".join(parts).strip()
        except Exception:
            return ""


class OpenAIVisionClient:
    """Vision client for OpenAI GPT-4o and OpenAI-compatible endpoints."""

    def __init__(
        self,
        api_key: str,
        model: str = "gpt-4o",
        base_url: Optional[str] = None,
        timeout: float = 30.0,
    ):
        self.api_key = api_key
        self.model = model
        self.timeout = timeout

        if base_url:
            self.base_url = base_url.rstrip("/") + "/chat/completions"
        else:
            self.base_url = "https://api.openai.com/v1/chat/completions"

    async def analyze_screenshot(
        self,
        base64_image: str,
        target_description: str,
        screen_width: int = 0,
        screen_height: int = 0,
    ) -> VisionResult:
        """Send screenshot to OpenAI / custom Vision API."""
        system_prompt = build_vision_prompt(
            target_description, screen_width, screen_height
        )

        payload = {
            "model": self.model,
            "max_tokens": 1024,
            "messages": [
                {"role": "system", "content": system_prompt},
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:image/png;base64,{base64_image}",
                                "detail": "high",
                            },
                        },
                        {
                            "type": "text",
                            "text": f"Find this UI element: {target_description}",
                        },
                    ],
                },
            ],
        }

        try:
            async with httpx.AsyncClient() as client:
                resp = await client.post(
                    self.base_url,
                    json=payload,
                    headers={
                        "Authorization": f"Bearer {self.api_key}",
                        "Content-Type": "application/json",
                    },
                    timeout=self.timeout,
                )
                resp.raise_for_status()
                data = resp.json()

            choices = data.get("choices", [])
            if not choices:
                return VisionResult(
                    found=False,
                    raw_response=json.dumps(data),
                    error="Vision model returned empty response",
                )

            raw_text = choices[0].get("message", {}).get("content", "").strip()
            if not raw_text:
                return VisionResult(
                    found=False,
                    raw_response=json.dumps(data),
                    error="Vision model returned empty response",
                )

            return _parse_vision_response(raw_text)

        except httpx.HTTPStatusError as e:
            return VisionResult(
                found=False,
                error=f"Vision API HTTP error {e.response.status_code}: {e.response.text[:500]}",
            )
        except httpx.TimeoutException:
            return VisionResult(
                found=False,
                error=f"Vision API request timed out after {self.timeout}s",
            )
        except Exception as e:
            return VisionResult(
                found=False,
                error=f"Vision API error: {e}",
            )

    async def chat(self, system_prompt: str, messages: list[dict]) -> str:
        """Send a plain-text chat request to the OpenAI / custom chat API.

        Returns the assistant's text reply (empty string if none).
        Raises on transport/HTTP errors; callers are expected to handle them.
        """
        payload = {
            "model": self.model,
            "max_tokens": 1024,
            "messages": [{"role": "system", "content": system_prompt}, *messages],
        }

        async with httpx.AsyncClient() as client:
            resp = await client.post(
                self.base_url,
                json=payload,
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json",
                },
                timeout=self.timeout,
            )
            resp.raise_for_status()
            data = resp.json()

        choices = data.get("choices", [])
        if not choices:
            return ""
        return (choices[0].get("message", {}).get("content", "") or "").strip()

    async def describe_screenshot(
        self, base64_image: str, question: str = "Describe the current screen."
    ) -> str:
        """Return a free-form text description of a screenshot (multimodal)."""
        payload = {
            "model": self.model,
            "max_tokens": 1024,
            "messages": [
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:image/png;base64,{base64_image}",
                                "detail": "high",
                            },
                        },
                        {"type": "text", "text": question},
                    ],
                }
            ],
        }
        try:
            async with httpx.AsyncClient() as client:
                resp = await client.post(
                    self.base_url,
                    json=payload,
                    headers={
                        "Authorization": f"Bearer {self.api_key}",
                        "Content-Type": "application/json",
                    },
                    timeout=self.timeout,
                )
                resp.raise_for_status()
                data = resp.json()
            choices = data.get("choices", [])
            if not choices:
                return ""
            return (choices[0].get("message", {}).get("content", "") or "").strip()
        except Exception:
            return ""


def create_vision_client() -> Optional[VisionClient]:
    """Create a vision client from configuration.

    Returns None if VISION_API_KEY is not configured.
    """
    from android_mcp.config import config

    if not config.VISION_API_KEY:
        return None

    provider = config.VISION_PROVIDER.lower().strip()

    if provider == "anthropic":
        return AnthropicVisionClient(
            api_key=config.VISION_API_KEY,
            model=config.VISION_MODEL or "claude-sonnet-5",
        )
    elif provider == "openai":
        return OpenAIVisionClient(
            api_key=config.VISION_API_KEY,
            model=config.VISION_MODEL or "gpt-4o",
        )
    elif provider == "custom":
        return OpenAIVisionClient(
            api_key=config.VISION_API_KEY,
            model=config.VISION_MODEL or "gpt-4o",
            base_url=config.VISION_API_BASE or None,
        )
    else:
        return None
