import pytest

from app.access.context import (
    PrincipalContext,
    PrincipalContextError,
)


def make_context(
    **overrides,
) -> PrincipalContext:
    values = {
        "principal_id": 10,
        "organization_id": 20,
        "organization_slug": "empresa-a",
        "principal_kind": "user",
        "role": "member",
        "max_classification": "internal",
    }

    values.update(overrides)

    return PrincipalContext(**values)


def test_public_context_allows_only_public():
    context = make_context(
        max_classification="public",
    )

    assert (
        context.allowed_classifications
        == frozenset(
            {
                "public",
            }
        )
    )


def test_internal_context_allows_public_and_internal():
    context = make_context(
        max_classification="internal",
    )

    assert (
        context.allowed_classifications
        == frozenset(
            {
                "public",
                "internal",
            }
        )
    )


def test_confidential_context_allows_all_classifications():
    context = make_context(
        max_classification="confidential",
    )

    assert (
        context.allowed_classifications
        == frozenset(
            {
                "public",
                "internal",
                "confidential",
            }
        )
    )


def test_invalid_principal_id_is_rejected():
    with pytest.raises(
        PrincipalContextError,
        match="principal_id must be a positive integer",
    ):
        make_context(
            principal_id=0,
        )


def test_invalid_organization_id_is_rejected():
    with pytest.raises(
        PrincipalContextError,
        match="organization_id must be a positive integer",
    ):
        make_context(
            organization_id=0,
        )


def test_empty_organization_slug_is_rejected():
    with pytest.raises(
        PrincipalContextError,
        match="organization_slug must not be empty",
    ):
        make_context(
            organization_slug="   ",
        )


def test_organization_slug_is_normalized():
    context = make_context(
        organization_slug="  empresa-a  ",
    )

    assert (
        context.organization_slug
        == "empresa-a"
    )


def test_invalid_principal_kind_is_rejected():
    with pytest.raises(
        PrincipalContextError,
        match="Invalid principal kind",
    ):
        make_context(
            principal_kind="robot",
        )


def test_invalid_role_is_rejected():
    with pytest.raises(
        PrincipalContextError,
        match="Invalid organization role",
    ):
        make_context(
            role="superadmin",
        )


def test_invalid_max_classification_is_rejected():
    with pytest.raises(
        PrincipalContextError,
        match="Invalid maximum classification",
    ):
        make_context(
            max_classification="secret",
        )