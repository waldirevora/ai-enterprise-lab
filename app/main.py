from fastapi import FastAPI

from app.providers.catalog import get_provider_catalog
from app.schemas import GenerateRequest, GenerateResponse
from app.services.generation import generate_text


app = FastAPI(
    title="AI Enterprise Lab Gateway",
    version="0.1.0",
)


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/v1/providers")
def providers() -> dict:
    return get_provider_catalog()


@app.post("/v1/generate", response_model=GenerateResponse)
async def generate(request: GenerateRequest) -> GenerateResponse:
    return await generate_text(request)