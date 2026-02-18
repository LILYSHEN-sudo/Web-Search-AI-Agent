from typing import Optional

import httpx

from config import settings

BASE_URL = "https://sfo1.aihub.zeabur.ai"


class LLMError(Exception):
    """Exception raised for LLM API errors."""

    def __init__(self, message: str, status_code: Optional[int] = None):
        self.message = message
        self.status_code = status_code
        super().__init__(self.message)


class LLMClient:
    def __init__(
        self,
        api_token: Optional[str] = None,
        model: Optional[str] = None,
        base_url: str = BASE_URL,
    ):
        self.api_token = api_token or settings.zeabur_api_token
        self.model = model or settings.zeabur_model
        self.base_url = base_url

    def _get_headers(self) -> dict:
        return {
            "Authorization": f"Bearer {self.api_token}",
            "Content-Type": "application/json",
        }

    async def chat(
        self,
        messages: list[dict],
        model: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
    ) -> str:
        """
        Send a chat completion request with conversation history.

        Args:
            messages: List of message dicts with 'role' and 'content' keys.
                      Roles: 'system', 'user', 'assistant'
            model: Model to use (defaults to settings.zeabur_model)
            temperature: Sampling temperature (0-2)
            max_tokens: Maximum tokens in response

        Returns:
            The assistant's response text.

        Raises:
            LLMError: If the API request fails.
        """
        payload = {
            "model": model or self.model,
            "messages": messages,
            "temperature": temperature,
        }
        if max_tokens:
            payload["max_tokens"] = max_tokens

        try:
            async with httpx.AsyncClient(timeout=60.0) as client:
                response = await client.post(
                    f"{self.base_url}/v1/chat/completions",
                    headers=self._get_headers(),
                    json=payload,
                )

                if response.status_code != 200:
                    error_detail = response.text
                    try:
                        error_json = response.json()
                        error_detail = error_json.get("error", {}).get("message", error_detail)
                    except Exception:
                        pass
                    raise LLMError(
                        f"API request failed: {error_detail}",
                        status_code=response.status_code,
                    )

                data = response.json()
                return data["choices"][0]["message"]["content"]

        except httpx.TimeoutException:
            raise LLMError("Request timed out")
        except httpx.RequestError as e:
            raise LLMError(f"Request failed: {str(e)}")

    async def prompt(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        **kwargs,
    ) -> str:
        """
        Send a simple prompt and get a response.

        Args:
            prompt: The user's prompt text.
            system_prompt: Optional system instructions.
            **kwargs: Additional arguments passed to chat().

        Returns:
            The assistant's response text.
        """
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})

        return await self.chat(messages, **kwargs)


llm_client = LLMClient()
