import httpx


class OllamaEmbeddingProviderError(Exception):
    pass


class OllamaEmbeddingProvider:
    def __init__(
        self,
        base_url: str,
        expected_dimensions: int,
    ):
        self.base_url = base_url.rstrip("/")
        self.expected_dimensions = expected_dimensions

    async def embed(
        self,
        *,
        model: str,
        text: str,
    ) -> list[float]:
        payload = {
            "model": model,
            "input": text,
        }

        try:
            async with httpx.AsyncClient(timeout=120.0) as client:
                response = await client.post(
                    f"{self.base_url}/api/embed",
                    json=payload,
                )

                response.raise_for_status()

        except httpx.TimeoutException as exc:
            raise OllamaEmbeddingProviderError(
                "Ollama embedding request timed out."
            ) from exc

        except httpx.HTTPStatusError as exc:
            status_code = exc.response.status_code

            if status_code == 404:
                message = "Ollama embedding model not found."
            else:
                message = (
                    f"Ollama embedding API returned "
                    f"HTTP {status_code}."
                )

            raise OllamaEmbeddingProviderError(
                message
            ) from exc

        except httpx.RequestError as exc:
            raise OllamaEmbeddingProviderError(
                "Could not connect to Ollama embedding API."
            ) from exc

        result = response.json()

        embeddings = result.get("embeddings")

        if not embeddings:
            raise OllamaEmbeddingProviderError(
                "Ollama returned no embeddings."
            )

        embedding = embeddings[0]

        if len(embedding) != self.expected_dimensions:
            raise OllamaEmbeddingProviderError(
                "Unexpected embedding dimensions: "
                f"expected {self.expected_dimensions}, "
                f"received {len(embedding)}."
            )

        return embedding