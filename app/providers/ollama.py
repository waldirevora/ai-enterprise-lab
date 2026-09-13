import httpx


class OllamaProviderError(Exception):
    pass


class OllamaProvider:
    def __init__(
        self,
        base_url: str,
    ):
        self.base_url = base_url.rstrip("/")

    async def generate(
        self,
        *,
        model: str,
        prompt: str,
        temperature: float,
        num_ctx: int,
        max_output_tokens: int,
    ) -> dict:
        payload = {
            "model": model,
            "prompt": prompt,
            "stream": False,
            "options": {
                "temperature": temperature,
                "num_ctx": num_ctx,
                "num_predict": max_output_tokens,
            },
        }

        try:
            async with httpx.AsyncClient(timeout=120.0) as client:
                response = await client.post(
                    f"{self.base_url}/api/generate",
                    json=payload,
                )

                response.raise_for_status()

        except httpx.TimeoutException as exc:
            raise OllamaProviderError(
                "Ollama request timed out."
            ) from exc

        except httpx.HTTPStatusError as exc:
            status_code = exc.response.status_code

            if status_code == 404:
                message = "Ollama model not found."
            else:
                message = (
                    f"Ollama returned HTTP {status_code}."
                )

            raise OllamaProviderError(message) from exc

        except httpx.RequestError as exc:
            raise OllamaProviderError(
                "Could not connect to Ollama."
            ) from exc

        return response.json()