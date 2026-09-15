from dataclasses import dataclass
import re
import unicodedata

import psycopg

from app.access.context import PrincipalContext
from app.access.unit_grants import UnitAccessGrant
from app.db.postgres import build_postgres_dsn


class UnitScopeError(Exception):
    pass


class UnitScopeDeniedError(UnitScopeError):
    pass


class UnitScopeUnavailableError(UnitScopeError):
    pass


@dataclass(frozen=True)
class OrganizationalUnitReference:
    organizational_unit_id: int
    slug: str
    name: str


@dataclass(frozen=True)
class UnitScopeDecision:
    referenced_unit_ids: frozenset[int]
    unit_grants: tuple[UnitAccessGrant, ...]

    @property
    def has_explicit_unit_scope(self) -> bool:
        return bool(
            self.referenced_unit_ids
        )


def normalize_unit_text(
    value: str,
) -> str:
    normalized = unicodedata.normalize(
        "NFKD",
        value.casefold(),
    )

    without_accents = "".join(
        character
        for character in normalized
        if not unicodedata.combining(
            character
        )
    )

    alphanumeric_only = re.sub(
        r"[^a-z0-9]+",
        " ",
        without_accents,
    )

    return " ".join(
        alphanumeric_only.split()
    )


def _contains_normalized_phrase(
    *,
    normalized_text: str,
    normalized_phrase: str,
) -> bool:
    if not normalized_phrase:
        return False

    padded_text = (
        f" {normalized_text} "
    )

    padded_phrase = (
        f" {normalized_phrase} "
    )

    return (
        padded_phrase
        in padded_text
    )


def detect_referenced_unit_ids(
    *,
    question: str,
    units: tuple[
        OrganizationalUnitReference,
        ...,
    ],
) -> frozenset[int]:
    normalized_question = (
        normalize_unit_text(
            question
        )
    )

    if not normalized_question:
        return frozenset()

    detected: set[int] = set()

    for unit in units:
        aliases = {
            normalize_unit_text(
                unit.slug
            ),
            normalize_unit_text(
                unit.name
            ),
        }

        for alias in aliases:
            if _contains_normalized_phrase(
                normalized_text=(
                    normalized_question
                ),
                normalized_phrase=alias,
            ):
                detected.add(
                    unit.organizational_unit_id
                )

                break

    return frozenset(
        detected
    )


async def _load_active_units(
    *,
    organization_id: int,
) -> tuple[
    OrganizationalUnitReference,
    ...,
]:
    async with await psycopg.AsyncConnection.connect(
        build_postgres_dsn(),
        connect_timeout=5,
    ) as connection:
        async with connection.cursor() as cursor:
            await cursor.execute(
                """
                SELECT
                    id,
                    slug,
                    name
                FROM organizational_units
                WHERE organization_id = %s
                  AND status = 'active'
                ORDER BY id;
                """,
                (
                    organization_id,
                ),
            )

            rows = await cursor.fetchall()

    return tuple(
        OrganizationalUnitReference(
            organizational_unit_id=row[0],
            slug=row[1],
            name=row[2],
        )
        for row in rows
    )


async def resolve_unit_scope(
    *,
    context: PrincipalContext,
    question: str,
    unit_grants: tuple[
        UnitAccessGrant,
        ...,
    ],
) -> UnitScopeDecision:
    try:
        units = await _load_active_units(
            organization_id=(
                context.organization_id
            ),
        )

    except (
        psycopg.Error,
        OSError,
    ) as exc:
        raise UnitScopeUnavailableError(
            "Unit scope service unavailable."
        ) from exc

    referenced_unit_ids = (
        detect_referenced_unit_ids(
            question=question,
            units=units,
        )
    )

    #
    # Nenhuma unit explicitamente mencionada.
    #
    # Preserva todos os grants já autorizados
    # para o fluxo normal.
    #
    if not referenced_unit_ids:
        return UnitScopeDecision(
            referenced_unit_ids=(
                frozenset()
            ),
            unit_grants=unit_grants,
        )

    authorized_by_id = {
        grant.organizational_unit_id: grant
        for grant in unit_grants
    }

    unauthorized_ids = (
        referenced_unit_ids.difference(
            authorized_by_id
        )
    )

    #
    # Fail closed.
    #
    # Não informa ao cliente se a unidade
    # existe ou apenas não está autorizada.
    #
    if unauthorized_ids:
        raise UnitScopeDeniedError(
            "No authorized RAG context was found."
        )

    #
    # Quando a pergunta cita explicitamente
    # uma ou mais units autorizadas,
    # elimina grants de outras units.
    #
    scoped_grants = tuple(
        grant
        for grant in unit_grants
        if grant.organizational_unit_id
        in referenced_unit_ids
    )

    return UnitScopeDecision(
        referenced_unit_ids=(
            referenced_unit_ids
        ),
        unit_grants=scoped_grants,
    )