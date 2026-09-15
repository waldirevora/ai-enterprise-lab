import asyncio

import pytest

from app.access import authentication
from app.access.api_keys import (
    generate_api_key,
)
from app.access.authentication import (
    AuthenticationError,
    AuthenticationUnavailableError,
    CredentialCandidate,
    authenticate_api_key,
)


def make_candidate(
    *,
    secret_hash: str,
    credential_id: int = 100,
    principal_id: int = 10,
    principal_kind: str = "user",
    organization_id: int = 20,
    organization_slug: str = "empresa-a",
    role: str = "member",
    max_classification: str = "internal",
    is_revoked: bool = False,
    is_expired: bool = False,
    principal_active: bool = True,
    organization_active: bool = True,
    membership_active: bool = True,
) -> CredentialCandidate:
    return CredentialCandidate(
        credential_id=credential_id,
        secret_hash=secret_hash,
        principal_id=principal_id,
        principal_kind=principal_kind,
        organization_id=organization_id,
        organization_slug=organization_slug,
        role=role,
        max_classification=max_classification,
        is_revoked=is_revoked,
        is_expired=is_expired,
        principal_active=principal_active,
        organization_active=organization_active,
        membership_active=membership_active,
    )


def test_valid_api_key_returns_principal_context(
    monkeypatch,
):
    generated = generate_api_key()

    candidate = make_candidate(
        secret_hash=generated.secret_hash,
    )

    captured = {}

    async def fake_load(
        *,
        key_prefix,
    ):
        captured["key_prefix"] = (
            key_prefix
        )

        return [
            candidate,
        ]

    async def fake_mark(
        *,
        credential_id,
    ):
        captured["credential_id"] = (
            credential_id
        )

        return True

    monkeypatch.setattr(
        authentication,
        "_load_candidate_credentials",
        fake_load,
    )

    monkeypatch.setattr(
        authentication,
        "_mark_credential_used",
        fake_mark,
    )

    context = asyncio.run(
        authenticate_api_key(
            generated.token
        )
    )

    assert context.principal_id == 10
    assert context.organization_id == 20
    assert (
        context.organization_slug
        == "empresa-a"
    )
    assert context.role == "member"

    assert (
        context.allowed_classifications
        == frozenset(
            {
                "public",
                "internal",
            }
        )
    )

    assert (
        captured["key_prefix"]
        == generated.key_prefix
    )

    assert (
        captured["credential_id"]
        == 100
    )


def test_malformed_api_key_is_rejected_before_database(
    monkeypatch,
):
    async def should_not_load(
        *,
        key_prefix,
    ):
        raise AssertionError(
            "Database should not be queried."
        )

    monkeypatch.setattr(
        authentication,
        "_load_candidate_credentials",
        should_not_load,
    )

    with pytest.raises(
        AuthenticationError,
        match="Invalid API credential",
    ):
        asyncio.run(
            authenticate_api_key(
                "invalid-key"
            )
        )


def test_missing_credential_is_rejected(
    monkeypatch,
):
    generated = generate_api_key()

    async def fake_load(
        *,
        key_prefix,
    ):
        return []

    monkeypatch.setattr(
        authentication,
        "_load_candidate_credentials",
        fake_load,
    )

    with pytest.raises(
        AuthenticationError,
        match="Invalid API credential",
    ):
        asyncio.run(
            authenticate_api_key(
                generated.token
            )
        )


def test_wrong_api_key_hash_is_rejected(
    monkeypatch,
):
    requested = generate_api_key()
    stored = generate_api_key()

    async def fake_load(
        *,
        key_prefix,
    ):
        return [
            make_candidate(
                secret_hash=(
                    stored.secret_hash
                ),
            )
        ]

    monkeypatch.setattr(
        authentication,
        "_load_candidate_credentials",
        fake_load,
    )

    with pytest.raises(
        AuthenticationError,
        match="Invalid API credential",
    ):
        asyncio.run(
            authenticate_api_key(
                requested.token
            )
        )


def test_revoked_credential_is_rejected(
    monkeypatch,
):
    generated = generate_api_key()

    async def fake_load(
        *,
        key_prefix,
    ):
        return [
            make_candidate(
                secret_hash=(
                    generated.secret_hash
                ),
                is_revoked=True,
            )
        ]

    monkeypatch.setattr(
        authentication,
        "_load_candidate_credentials",
        fake_load,
    )

    with pytest.raises(
        AuthenticationError,
        match="Invalid API credential",
    ):
        asyncio.run(
            authenticate_api_key(
                generated.token
            )
        )


def test_expired_credential_is_rejected(
    monkeypatch,
):
    generated = generate_api_key()

    async def fake_load(
        *,
        key_prefix,
    ):
        return [
            make_candidate(
                secret_hash=(
                    generated.secret_hash
                ),
                is_expired=True,
            )
        ]

    monkeypatch.setattr(
        authentication,
        "_load_candidate_credentials",
        fake_load,
    )

    with pytest.raises(
        AuthenticationError,
        match="Invalid API credential",
    ):
        asyncio.run(
            authenticate_api_key(
                generated.token
            )
        )


def test_disabled_principal_is_rejected(
    monkeypatch,
):
    generated = generate_api_key()

    async def fake_load(
        *,
        key_prefix,
    ):
        return [
            make_candidate(
                secret_hash=(
                    generated.secret_hash
                ),
                principal_active=False,
            )
        ]

    monkeypatch.setattr(
        authentication,
        "_load_candidate_credentials",
        fake_load,
    )

    with pytest.raises(
        AuthenticationError,
        match="Invalid API credential",
    ):
        asyncio.run(
            authenticate_api_key(
                generated.token
            )
        )


def test_disabled_organization_is_rejected(
    monkeypatch,
):
    generated = generate_api_key()

    async def fake_load(
        *,
        key_prefix,
    ):
        return [
            make_candidate(
                secret_hash=(
                    generated.secret_hash
                ),
                organization_active=False,
            )
        ]

    monkeypatch.setattr(
        authentication,
        "_load_candidate_credentials",
        fake_load,
    )

    with pytest.raises(
        AuthenticationError,
        match="Invalid API credential",
    ):
        asyncio.run(
            authenticate_api_key(
                generated.token
            )
        )


def test_disabled_membership_is_rejected(
    monkeypatch,
):
    generated = generate_api_key()

    async def fake_load(
        *,
        key_prefix,
    ):
        return [
            make_candidate(
                secret_hash=(
                    generated.secret_hash
                ),
                membership_active=False,
            )
        ]

    monkeypatch.setattr(
        authentication,
        "_load_candidate_credentials",
        fake_load,
    )

    with pytest.raises(
        AuthenticationError,
        match="Invalid API credential",
    ):
        asyncio.run(
            authenticate_api_key(
                generated.token
            )
        )


def test_prefix_collision_selects_matching_hash(
    monkeypatch,
):
    generated = generate_api_key()

    other = generate_api_key()

    first_candidate = make_candidate(
        credential_id=1,
        secret_hash=other.secret_hash,
    )

    matching_candidate = make_candidate(
        credential_id=2,
        secret_hash=generated.secret_hash,
    )

    captured = {}

    async def fake_load(
        *,
        key_prefix,
    ):
        return [
            first_candidate,
            matching_candidate,
        ]

    async def fake_mark(
        *,
        credential_id,
    ):
        captured["credential_id"] = (
            credential_id
        )

        return True

    monkeypatch.setattr(
        authentication,
        "_load_candidate_credentials",
        fake_load,
    )

    monkeypatch.setattr(
        authentication,
        "_mark_credential_used",
        fake_mark,
    )

    context = asyncio.run(
        authenticate_api_key(
            generated.token
        )
    )

    assert context.principal_id == 10

    assert (
        captured["credential_id"]
        == 2
    )


def test_state_change_before_last_used_update_is_rejected(
    monkeypatch,
):
    generated = generate_api_key()

    async def fake_load(
        *,
        key_prefix,
    ):
        return [
            make_candidate(
                secret_hash=(
                    generated.secret_hash
                ),
            )
        ]

    async def fake_mark(
        *,
        credential_id,
    ):
        return False

    monkeypatch.setattr(
        authentication,
        "_load_candidate_credentials",
        fake_load,
    )

    monkeypatch.setattr(
        authentication,
        "_mark_credential_used",
        fake_mark,
    )

    with pytest.raises(
        AuthenticationError,
        match="Invalid API credential",
    ):
        asyncio.run(
            authenticate_api_key(
                generated.token
            )
        )


def test_database_lookup_failure_is_unavailable(
    monkeypatch,
):
    generated = generate_api_key()

    async def fake_load(
        *,
        key_prefix,
    ):
        raise OSError(
            "database unavailable"
        )

    monkeypatch.setattr(
        authentication,
        "_load_candidate_credentials",
        fake_load,
    )

    with pytest.raises(
        AuthenticationUnavailableError,
        match="Authentication service unavailable",
    ):
        asyncio.run(
            authenticate_api_key(
                generated.token
            )
        )


def test_last_used_update_failure_is_unavailable(
    monkeypatch,
):
    generated = generate_api_key()

    async def fake_load(
        *,
        key_prefix,
    ):
        return [
            make_candidate(
                secret_hash=(
                    generated.secret_hash
                ),
            )
        ]

    async def fake_mark(
        *,
        credential_id,
    ):
        raise OSError(
            "database unavailable"
        )

    monkeypatch.setattr(
        authentication,
        "_load_candidate_credentials",
        fake_load,
    )

    monkeypatch.setattr(
        authentication,
        "_mark_credential_used",
        fake_mark,
    )

    with pytest.raises(
        AuthenticationUnavailableError,
        match="Authentication service unavailable",
    ):
        asyncio.run(
            authenticate_api_key(
                generated.token
            )
        )