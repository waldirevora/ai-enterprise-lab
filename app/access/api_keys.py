from dataclasses import dataclass
import hashlib
import hmac
import re
import secrets


API_KEY_MARKER = "ael_"
API_KEY_SECRET_BYTES = 32
API_KEY_PREFIX_LENGTH = 16

_TOKEN_PATTERN = re.compile(
    r"^ael_[A-Za-z0-9_-]{43}$"
)

_HASH_PATTERN = re.compile(
    r"^[0-9a-f]{64}$"
)


class ApiKeyError(ValueError):
    pass


@dataclass(frozen=True)
class GeneratedApiKey:
    token: str
    key_prefix: str
    secret_hash: str


def _validate_api_key(
    token: str,
) -> str:
    if not isinstance(token, str):
        raise ApiKeyError(
            "API key must be a string."
        )

    if _TOKEN_PATTERN.fullmatch(token) is None:
        raise ApiKeyError(
            "Invalid API key format."
        )

    return token


def hash_api_key(
    token: str,
) -> str:
    validated_token = _validate_api_key(
        token
    )

    return hashlib.sha256(
        validated_token.encode("utf-8")
    ).hexdigest()


def extract_key_prefix(
    token: str,
) -> str:
    validated_token = _validate_api_key(
        token
    )

    return validated_token[
        :API_KEY_PREFIX_LENGTH
    ]


def verify_api_key(
    token: str,
    expected_hash: str,
) -> bool:
    try:
        validated_token = (
            _validate_api_key(token)
        )

    except ApiKeyError:
        return False

    if not isinstance(
        expected_hash,
        str,
    ):
        return False

    if (
        _HASH_PATTERN.fullmatch(
            expected_hash
        )
        is None
    ):
        return False

    computed_hash = hashlib.sha256(
        validated_token.encode("utf-8")
    ).hexdigest()

    return hmac.compare_digest(
        computed_hash,
        expected_hash,
    )


def generate_api_key() -> GeneratedApiKey:
    secret = secrets.token_urlsafe(
        API_KEY_SECRET_BYTES
    )

    token = (
        f"{API_KEY_MARKER}{secret}"
    )

    return GeneratedApiKey(
        token=token,
        key_prefix=extract_key_prefix(
            token
        ),
        secret_hash=hash_api_key(
            token
        ),
    )