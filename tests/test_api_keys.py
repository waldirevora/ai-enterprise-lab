import pytest

from app.access.api_keys import (
    API_KEY_PREFIX_LENGTH,
    ApiKeyError,
    extract_key_prefix,
    generate_api_key,
    hash_api_key,
    verify_api_key,
)


def test_generated_api_key_has_expected_format():
    generated = generate_api_key()

    assert generated.token.startswith(
        "ael_"
    )

    assert (
        len(generated.key_prefix)
        == API_KEY_PREFIX_LENGTH
    )

    assert generated.key_prefix == (
        generated.token[
            :API_KEY_PREFIX_LENGTH
        ]
    )

    assert len(
        generated.secret_hash
    ) == 64

    int(
        generated.secret_hash,
        16,
    )


def test_generated_api_keys_are_unique():
    first = generate_api_key()
    second = generate_api_key()

    assert (
        first.token
        != second.token
    )

    assert (
        first.secret_hash
        != second.secret_hash
    )


def test_hash_is_deterministic():
    generated = generate_api_key()

    first = hash_api_key(
        generated.token
    )

    second = hash_api_key(
        generated.token
    )

    assert first == second


def test_correct_api_key_is_verified():
    generated = generate_api_key()

    assert verify_api_key(
        generated.token,
        generated.secret_hash,
    ) is True


def test_wrong_api_key_is_rejected():
    first = generate_api_key()
    second = generate_api_key()

    assert verify_api_key(
        second.token,
        first.secret_hash,
    ) is False


def test_malformed_api_key_is_rejected():
    assert verify_api_key(
        "invalid-key",
        "0" * 64,
    ) is False


def test_malformed_stored_hash_is_rejected():
    generated = generate_api_key()

    assert verify_api_key(
        generated.token,
        "not-a-valid-hash",
    ) is False


def test_key_prefix_can_be_extracted():
    generated = generate_api_key()

    assert extract_key_prefix(
        generated.token
    ) == generated.key_prefix


def test_whitespace_is_not_silently_accepted():
    generated = generate_api_key()

    with pytest.raises(
        ApiKeyError,
        match="Invalid API key format",
    ):
        hash_api_key(
            f" {generated.token}"
        )


def test_generated_hash_matches_token():
    generated = generate_api_key()

    assert generated.secret_hash == (
        hash_api_key(
            generated.token
        )
    )

    assert (
        generated.secret_hash
        != generated.token
    )