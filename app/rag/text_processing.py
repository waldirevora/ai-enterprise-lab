from dataclasses import dataclass
from hashlib import sha256


@dataclass(frozen=True)
class TextChunk:
    index: int
    content: str
    word_count: int
    start_word: int
    end_word: int


def normalize_text(text: str) -> str:
    text = text.replace("\r\n", "\n")
    text = text.replace("\r", "\n")

    normalized_lines: list[str] = []
    previous_blank = False

    for line in text.split("\n"):
        normalized_line = " ".join(line.split())

        if not normalized_line:
            if normalized_lines and not previous_blank:
                normalized_lines.append("")

            previous_blank = True
            continue

        normalized_lines.append(normalized_line)
        previous_blank = False

    while normalized_lines and not normalized_lines[-1]:
        normalized_lines.pop()

    return "\n".join(normalized_lines).strip()


def calculate_content_hash(text: str) -> str:
    normalized = normalize_text(text)

    return sha256(
        normalized.encode("utf-8")
    ).hexdigest()


def chunk_text(
    text: str,
    *,
    chunk_size_words: int = 220,
    overlap_words: int = 40,
) -> list[TextChunk]:
    if chunk_size_words <= 0:
        raise ValueError(
            "chunk_size_words must be greater than zero."
        )

    if overlap_words < 0:
        raise ValueError(
            "overlap_words cannot be negative."
        )

    if overlap_words >= chunk_size_words:
        raise ValueError(
            "overlap_words must be smaller than "
            "chunk_size_words."
        )

    normalized = normalize_text(text)

    if not normalized:
        return []

    words = normalized.split()

    chunks: list[TextChunk] = []

    start = 0
    index = 0

    while start < len(words):
        end = min(
            start + chunk_size_words,
            len(words),
        )

        chunk_words = words[start:end]

        chunks.append(
            TextChunk(
                index=index,
                content=" ".join(chunk_words),
                word_count=len(chunk_words),
                start_word=start,
                end_word=end,
            )
        )

        if end >= len(words):
            break

        start = end - overlap_words
        index += 1

    return chunks