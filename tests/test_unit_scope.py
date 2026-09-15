import asyncio

import pytest

from app.access import unit_scope
from app.access.context import (
    PrincipalContext,
)
from app.access.unit_grants import (
    UnitAccessGrant,
)
from app.access.unit_scope import (
    OrganizationalUnitReference,
    UnitScopeDeniedError,
    UnitScopeUnavailableError,
    detect_referenced_unit_ids,
    normalize_unit_text,
    resolve_unit_scope,
)


def make_context() -> PrincipalContext:
    return PrincipalContext(
        principal_id=10,
        organization_id=20,
        organization_slug="empresa-a",
        principal_kind="user",
        role="member",
        max_classification="internal",
    )


def make_unit(
    *,
    unit_id: int,
    slug: str,
    name: str,
) -> OrganizationalUnitReference:
    return OrganizationalUnitReference(
        organizational_unit_id=unit_id,
        slug=slug,
        name=name,
    )


def make_grant(
    *,
    unit_id: int,
    slug: str,
    name: str,
) -> UnitAccessGrant:
    return UnitAccessGrant(
        organizational_unit_id=unit_id,
        unit_slug=slug,
        unit_name=name,
        role="member",
        effective_max_classification=(
            "internal"
        ),
    )


def test_normalize_unit_text():
    assert (
        normalize_unit_text(
            "  Recursos-HUMANOS  "
        )
        == "recursos humanos"
    )

    assert (
        normalize_unit_text(
            "Operações"
        )
        == "operacoes"
    )


def test_detect_references_uses_word_boundaries():
    units = (
        make_unit(
            unit_id=1,
            slug="ti",
            name="TI",
        ),
        make_unit(
            unit_id=2,
            slug="rh",
            name="RH",
        ),
    )

    not_detected = (
        detect_referenced_unit_ids(
            question=(
                "Este documento está ativo."
            ),
            units=units,
        )
    )

    assert not_detected == frozenset()

    detected = (
        detect_referenced_unit_ids(
            question=(
                "Qual é o documento da TI?"
            ),
            units=units,
        )
    )

    assert detected == frozenset(
        {
            1,
        }
    )


def test_no_reference_preserves_all_grants(
    monkeypatch,
):
    units = (
        make_unit(
            unit_id=1,
            slug="financeiro",
            name="Financeiro",
        ),
        make_unit(
            unit_id=2,
            slug="rh",
            name="RH",
        ),
    )

    async def fake_load_active_units(
        *,
        organization_id,
    ):
        assert organization_id == 20
        return units

    monkeypatch.setattr(
        unit_scope,
        "_load_active_units",
        fake_load_active_units,
    )

    grants = (
        make_grant(
            unit_id=1,
            slug="financeiro",
            name="Financeiro",
        ),
        make_grant(
            unit_id=2,
            slug="rh",
            name="RH",
        ),
    )

    decision = asyncio.run(
        resolve_unit_scope(
            context=make_context(),
            question=(
                "Quais informações "
                "corporativas existem?"
            ),
            unit_grants=grants,
        )
    )

    assert (
        decision.referenced_unit_ids
        == frozenset()
    )

    assert (
        decision.unit_grants
        == grants
    )

    assert (
        decision.has_explicit_unit_scope
        is False
    )


def test_authorized_reference_restricts_grants(
    monkeypatch,
):
    units = (
        make_unit(
            unit_id=1,
            slug="financeiro",
            name="Financeiro",
        ),
        make_unit(
            unit_id=2,
            slug="rh",
            name="RH",
        ),
    )

    async def fake_load_active_units(
        *,
        organization_id,
    ):
        return units

    monkeypatch.setattr(
        unit_scope,
        "_load_active_units",
        fake_load_active_units,
    )

    financeiro = make_grant(
        unit_id=1,
        slug="financeiro",
        name="Financeiro",
    )

    rh = make_grant(
        unit_id=2,
        slug="rh",
        name="RH",
    )

    decision = asyncio.run(
        resolve_unit_scope(
            context=make_context(),
            question=(
                "Qual é o código "
                "do Financeiro?"
            ),
            unit_grants=(
                financeiro,
                rh,
            ),
        )
    )

    assert (
        decision.referenced_unit_ids
        == frozenset(
            {
                1,
            }
        )
    )

    assert (
        decision.unit_grants
        == (
            financeiro,
        )
    )

    assert (
        decision.has_explicit_unit_scope
        is True
    )


def test_unauthorized_reference_is_denied(
    monkeypatch,
):
    units = (
        make_unit(
            unit_id=1,
            slug="financeiro",
            name="Financeiro",
        ),
        make_unit(
            unit_id=2,
            slug="rh",
            name="RH",
        ),
    )

    async def fake_load_active_units(
        *,
        organization_id,
    ):
        return units

    monkeypatch.setattr(
        unit_scope,
        "_load_active_units",
        fake_load_active_units,
    )

    financeiro = make_grant(
        unit_id=1,
        slug="financeiro",
        name="Financeiro",
    )

    with pytest.raises(
        UnitScopeDeniedError,
        match=(
            "No authorized RAG "
            "context was found"
        ),
    ):
        asyncio.run(
            resolve_unit_scope(
                context=make_context(),
                question=(
                    "Qual é o código "
                    "oficial do RH?"
                ),
                unit_grants=(
                    financeiro,
                ),
            )
        )


def test_multiple_references_fail_closed(
    monkeypatch,
):
    units = (
        make_unit(
            unit_id=1,
            slug="financeiro",
            name="Financeiro",
        ),
        make_unit(
            unit_id=2,
            slug="rh",
            name="RH",
        ),
    )

    async def fake_load_active_units(
        *,
        organization_id,
    ):
        return units

    monkeypatch.setattr(
        unit_scope,
        "_load_active_units",
        fake_load_active_units,
    )

    financeiro = make_grant(
        unit_id=1,
        slug="financeiro",
        name="Financeiro",
    )

    with pytest.raises(
        UnitScopeDeniedError,
    ):
        asyncio.run(
            resolve_unit_scope(
                context=make_context(),
                question=(
                    "Compare Financeiro e RH."
                ),
                unit_grants=(
                    financeiro,
                ),
            )
        )


def test_loader_failure_is_unavailable(
    monkeypatch,
):
    async def fake_load_active_units(
        *,
        organization_id,
    ):
        raise OSError(
            "database unavailable"
        )

    monkeypatch.setattr(
        unit_scope,
        "_load_active_units",
        fake_load_active_units,
    )

    with pytest.raises(
        UnitScopeUnavailableError,
        match=(
            "Unit scope service "
            "unavailable"
        ),
    ):
        asyncio.run(
            resolve_unit_scope(
                context=make_context(),
                question="Financeiro",
                unit_grants=(),
            )
        )