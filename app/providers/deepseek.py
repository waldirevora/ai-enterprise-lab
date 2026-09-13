import httpx
from time import perf_counter


class DeepSeekProviderError(Exception):
    pass


class DeepSeekProvider:
    def __init__(
        self,
        *,
        base_url: str,
        api_key: str,
        thinking_enabled: bool,
        reasoning_effort: str,
    ):
        self.base_url = base_url.rstrip("/")
        self.api_key = api_key
        self.thinking_enabled = thinking_enabled
        self.reasoning_effort = reasoning_effort

    async def generate(
        self,
        *,
        model: str,
        prompt: str,
        max_output_tokens: int,
    ) -> dict:
        if not self.api_key:
            raise DeepSeekProviderError(
                "DeepSeek API key is not configured."
            )

        payload = {
            "model": model,
            "messages": [
                {
                    "role": "user",
                    "content": prompt,
                }
            ],
            "stream": False,
            "thinking": {
                "type": (
                    "enabled"
                    if self.thinking_enabled
                    else "disabled"
                )
            },
            "reasoning_effort": self.reasoning_effort,
            "max_tokens": max_output_tokens,
        }

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

        started_at = perf_counter()

        try:
            async with httpx.AsyncClient(timeout=180.0) as client:
                response = await client.post(
                    f"{self.base_url}/chat/completions",
                    headers=headers,
                    json=payload,
                )

                response.raise_for_status()

        except httpx.TimeoutException as exc:
            raise DeepSeekProviderError(
                "DeepSeek request timed out."
            ) from exc

        except httpx.HTTPStatusError as exc:
            status_code = exc.response.status_code

            if status_code == 401:
                message = "DeepSeek authentication failed."
            elif status_code == 429:
                message = "DeepSeek rate limit reached."
            else:
                message = (
                    f"DeepSeek returned HTTP {status_code}."
                )

            raise DeepSeekProviderError(message) from exc

        except httpx.RequestError as exc:
            raise DeepSeekProviderError(
                "Could not connect to DeepSeek."
            ) from exc

        result = response.json()

        result["_gateway_duration_ms"] = round(
            (perf_counter() - started_at) * 1000,
            2,
        )

        return result