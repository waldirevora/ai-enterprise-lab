from dataclasses import dataclass

import psycopg

from app.access.context import (
    DataClassification,
    PrincipalContext,
)
from app.db.postgres import build_postgres_dsn


class UnitGrantUnavailableError(Exception):
    pass


_CLASSIFICATION_RANK = {
    "public": 0,
    "internal": 1,
    "confidential": 2,
}


_CLASSIFICATION_ACCESS = {
    "public": frozenset(
        {
            "public",
        }
    ),
    "internal": frozenset(
        {
            "public",
            "internal",
        }
    ),
    "confidential": frozenset(
        {
            "public",
            "internal",
            "confidential",
        }
    ),
}


@dataclass(frozen=True)
class UnitMembershipRecord:
    organizational_unit_id: int
    unit_slug: str
    unit_name: str
    role: str
    organization_max_classification: str
    unit_max_classification: str


@dataclass(frozen=True)
class UnitAccessGrant:
    organizational_unit_id: int
    unit_slug: str
    unit_name: str
    role: str
    effective_max_classification: DataClassification

    @property
    def allowed_classifications(
        self,
    ) -> frozenset[str]:
        return _CLASSIFICATION_ACCESS[
            self.effective_max_classification
        ]


def _minimum_classification(
    *values: str,
) -> DataClassification:
    if not values:
        raise UnitGrantUnavailableError(
            "Unit authorization data is invalid."
        )

    try:
        lowest = min(
            values,
            key=lambda value: (
                _CLASSIFICATION_RANK[value]
            ),
        )

    except KeyError as exc:
        raise UnitGrantUnavailableError(
            "Unit authorization data is invalid."
        ) from exc

    return lowest


async def _load_unit_memberships(
    *,
    organization_id: int,
    principal_id: int,
) -> list[UnitMembershipRecord]:
    async with await psycopg.AsyncConnection.connect(
        build_postgres_dsn(),
        connect_timeout=5,
    ) as connection:
        async with connection.cursor() as cursor:
            await cursor.execute(
                """
                SELECT
                    u.id,
                    u.slug,
                    u.name,
                    pum.role,
                    om.max_classification,
                    pum.max_classification

                FROM principal_unit_memberships pum

                JOIN organizational_units u
                    ON u.organization_id
                        = pum.organization_id
                    AND u.id
                        = pum.organizational_unit_id

                JOIN organization_memberships om
                    ON om.organization_id
                        = pum.organization_id
                    AND om.principal_id
                        = pum.principal_id

                WHERE pum.organization_id = %s
                  AND pum.principal_id = %s
                  AND pum.status = 'active'
                  AND u.status = 'active'
                  AND om.status = 'active'

                ORDER BY u.id;
                """,
                (
                    organization_id,
                    principal_id,
                ),
            )

            rows = await cursor.fetchall()

    return [
        UnitMembershipRecord(
            organizational_unit_id=row[0],
            unit_slug=row[1],
            unit_name=row[2],
            role=row[3],
            organization_max_classification=row[4],
            unit_max_classification=row[5],
        )
        for row in rows
    ]


async def load_unit_access_grants(
    context: PrincipalContext,
) -> tuple[UnitAccessGrant, ...]:
    try:
        memberships = await _load_unit_memberships(
            organization_id=(
                context.organization_id
            ),
            principal_id=(
                context.principal_id
            ),
        )

    except (
        psycopg.Error,
        OSError,
    ) as exc:
        raise UnitGrantUnavailableError(
            "Unit authorization service unavailable."
        ) from exc

    grants: list[UnitAccessGrant] = []

    for membership in memberships:
        effective_max = _minimum_classification(
            context.max_classification,
            membership.organization_max_classification,
            membership.unit_max_classification,
        )

        grants.append(
            UnitAccessGrant(
                organizational_unit_id=(
                    membership.organizational_unit_id
                ),
                unit_slug=membership.unit_slug,
                unit_name=membership.unit_name,
                role=membership.role,
                effective_max_classification=(
                    effective_max
                ),
            )
        )

    return tuple(grants)