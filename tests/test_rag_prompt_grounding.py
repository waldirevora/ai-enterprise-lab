from app.rag.context_builder import RagContext
from app.rag.service import build_augmented_prompt


def make_context() -> RagContext:
    return RagContext(
        text=(
            "Documento corporativo autorizado. "
            "Código corporativo: CORP-123."
        ),
        chunks_used=1,
        characters_used=58,
        effective_classification="internal",
        document_ids=(1,),
    )


def test_prompt_forbids_entity_substitution():
    prompt = build_augmented_prompt(
        question=(
            "Qual é o código oficial do RH?"
        ),
        context=make_context(),
    )

    assert (
        "Never substitute information about "
        "a different department"
        in prompt
    )

    assert (
        "do not use it as a replacement"
        in prompt
    )


def test_prompt_requires_insufficient_context_response():
    prompt = build_augmented_prompt(
        question=(
            "Qual é o código oficial do RH?"
        ),
        context=make_context(),
    )

    assert (
        "cannot be determined from the "
        "authorized context"
        in prompt
    )

    assert (
        "specific entity or information "
        "requested"
        in prompt
    )