import asyncio

import pytest

from app.access import unit_grants
from app.access.context import PrincipalContext
from app.access.unit_grants import (
    UnitGrantUnavailableError,
    UnitMembershipRecord,
    load_unit_access_grants,
)


def make_context(
    *,
    max_classification="confidential",
) -> PrincipalContext:
    return PrincipalContext(
        principal_id=10,
        organization_id=20,
        organization_slug="empresa-a",
        principal_kind="user",
        role="member",
        max_classification=max_classification,
    )


def make_membership(
    *,
    organizational_unit_id=100,
    unit_slug="financeiro",
    unit_name="Financeiro",
    role="member",
    organization_max_classification="confidential",
    unit_max_classification="internal",
) -> UnitMembershipRecord:
    return UnitMembershipRecord(
        organizational_unit_id=(
            organizational_unit_id
        ),
        unit_slug=unit_slug,
        unit_name=unit_name,
        role=role,
        organization_max_classification=(
            organization_max_classification
        ),
        unit_max_classification=(
            unit_max_classification
        ),
    )


def test_public_is_lowest_classification():
    result = (
        unit_grants._minimum_classification(
            "confidential",
            "internal",
            "public",
        )
    )

    assert result == "public"


def test_unit_can_reduce_organization_limit():
    result = (
        unit_grants._minimum_classification(
            "confidential",
            "confidential",
            "internal",
        )
    )

    assert result == "internal"


def test_unit_cannot_raise_context_limit():
    result = (
        unit_grants._minimum_classification(
            "internal",
            "internal",
            "confidential",
        )
    )

    assert result == "internal"


def test_confidential_remains_confidential():
    result = (
        unit_grants._minimum_classification(
            "confidential",
            "confidential",
            "confidential",
        )
    )

    assert result == "confidential"


def test_load_unit_access_grants(
    monkeypatch,
):
    async def fake_load(
        *,
        organization_id,
        principal_id,
    ):
        assert organization_id == 20
        assert principal_id == 10

        return [
            make_membership(
                organizational_unit_id=100,
                unit_slug="financeiro",
                unit_name="Financeiro",
                unit_max_classification="internal",
            ),
            make_membership(
                organizational_unit_id=200,
                unit_slug="rh",
                unit_name="RH",
                unit_max_classification="public",
            ),
        ]

    monkeypatch.setattr(
        unit_grants,
        "_load_unit_memberships",
        fake_load,
    )

    grants = asyncio.run(
        load_unit_access_grants(
            make_context()
        )
    )

    assert len(grants) == 2

    financeiro = grants[0]
    rh = grants[1]

    assert (
        financeiro.organizational_unit_id
        == 100
    )

    assert (
        financeiro.effective_max_classification
        == "internal"
    )

    assert (
        financeiro.allowed_classifications
        == frozenset(
            {
                "public",
                "internal",
            }
        )
    )

    assert (
        rh.organizational_unit_id
        == 200
    )

    assert (
        rh.effective_max_classification
        == "public"
    )

    assert (
        rh.allowed_classifications
        == frozenset(
            {
                "public",
            }
        )
    )


def test_no_unit_memberships_returns_empty_tuple(
    monkeypatch,
):
    async def fake_load(
        *,
        organization_id,
        principal_id,
    ):
        return []

    monkeypatch.setattr(
        unit_grants,
        "_load_unit_memberships",
        fake_load,
    )

    grants = asyncio.run(
        load_unit_access_grants(
            make_context()
        )
    )

    assert grants == ()


def test_database_failure_is_unavailable(
    monkeypatch,
):
    async def fake_load(
        *,
        organization_id,
        principal_id,
    ):
        raise OSError(
            "database unavailable"
        )

    monkeypatch.setattr(
        unit_grants,
        "_load_unit_memberships",
        fake_load,
    )

    with pytest.raises(
        UnitGrantUnavailableError,
        match=(
            "Unit authorization service "
            "unavailable"
        ),
    ):
        asyncio.run(
            load_unit_access_grants(
                make_context()
            )
        )