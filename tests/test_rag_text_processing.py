import pytest

from app.rag.text_processing import (
    calculate_content_hash,
    chunk_text,
    normalize_text,
)


def test_normalize_text():
    text = (
        "  Inteligencia   artificial  \r\n"
        "\r\n"
        "\r\n"
        "Automacao    empresarial "
    )

    result = normalize_text(text)

    assert result == (
        "Inteligencia artificial\n\n"
        "Automacao empresarial"
    )


def test_content_hash_is_deterministic():
    first = calculate_content_hash(
        "Inteligencia   artificial"
    )

    second = calculate_content_hash(
        "Inteligencia artificial"
    )

    assert first == second
    assert len(first) == 64


def test_different_content_has_different_hash():
    first = calculate_content_hash(
        "Documento A"
    )

    second = calculate_content_hash(
        "Documento B"
    )

    assert first != second


def test_chunking_with_overlap():
    text = " ".join(
        f"word{i}"
        for i in range(10)
    )

    chunks = chunk_text(
        text,
        chunk_size_words=4,
        overlap_words=1,
    )

    assert len(chunks) == 3

    assert chunks[0].content == (
        "word0 word1 word2 word3"
    )

    assert chunks[1].content == (
        "word3 word4 word5 word6"
    )

    assert chunks[2].content == (
        "word6 word7 word8 word9"
    )

    assert chunks[0].index == 0
    assert chunks[1].index == 1
    assert chunks[2].index == 2


def test_empty_text_returns_no_chunks():
    assert chunk_text("   \n\n ") == []


def test_invalid_overlap_is_rejected():
    with pytest.raises(
        ValueError,
        match="overlap_words must be smaller",
    ):
        chunk_text(
            "teste",
            chunk_size_words=10,
            overlap_words=10,
        )