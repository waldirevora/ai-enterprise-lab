import pytest

from app.access.unit_grants import (
    UnitAccessGrant,
)
from app.rag.retrieval import (
    RagRetrievalError,
    _build_scope_filter,
    _normalize_unit_grants,
)


def make_grant(
    *,
    unit_id: int,
    classification: str,
) -> UnitAccessGrant:
    return UnitAccessGrant(
        organizational_unit_id=unit_id,
        unit_slug=f"unit-{unit_id}",
        unit_name=f"Unit {unit_id}",
        role="member",
        effective_max_classification=(
            classification
        ),
    )


def test_corporate_scope_is_always_present():
    sql, params = _build_scope_filter(
        corporate_allowed_classifications=(
            frozenset(
                {
                    "public",
                    "internal",
                }
            )
        ),
        unit_grants=(),
    )

    assert (
        "d.organizational_unit_id IS NULL"
        in sql
    )

    assert params == [
        [
            "internal",
            "public",
        ]
    ]


def test_unit_scope_uses_unit_specific_classification():
    financeiro = make_grant(
        unit_id=10,
        classification="internal",
    )

    sql, params = _build_scope_filter(
        corporate_allowed_classifications=(
            frozenset(
                {
                    "public",
                    "internal",
                    "confidential",
                }
            )
        ),
        unit_grants=(
            financeiro,
        ),
    )

    assert (
        "d.organizational_unit_id = %s"
        in sql
    )

    assert params == [
        [
            "confidential",
            "internal",
            "public",
        ],
        10,
        [
            "internal",
            "public",
        ],
    ]


def test_units_keep_independent_limits():
    financeiro = make_grant(
        unit_id=10,
        classification="internal",
    )

    rh = make_grant(
        unit_id=20,
        classification="public",
    )

    _, params = _build_scope_filter(
        corporate_allowed_classifications=(
            frozenset(
                {
                    "public",
                    "internal",
                    "confidential",
                }
            )
        ),
        unit_grants=(
            financeiro,
            rh,
        ),
    )

    assert params == [
        [
            "confidential",
            "internal",
            "public",
        ],
        10,
        [
            "internal",
            "public",
        ],
        20,
        [
            "public",
        ],
    ]


def test_duplicate_unit_grants_use_intersection():
    wider = make_grant(
        unit_id=10,
        classification="internal",
    )

    narrower = make_grant(
        unit_id=10,
        classification="public",
    )

    normalized = _normalize_unit_grants(
        (
            wider,
            narrower,
        )
    )

    assert normalized == (
        (
            10,
            frozenset(
                {
                    "public",
                }
            ),
        ),
    )


def test_invalid_unit_id_is_rejected():
    invalid = make_grant(
        unit_id=0,
        classification="public",
    )

    with pytest.raises(
        RagRetrievalError,
        match=(
            "organizational_unit_id must be "
            "a positive integer"
        ),
    ):
        _normalize_unit_grants(
            (
                invalid,
            )
        )