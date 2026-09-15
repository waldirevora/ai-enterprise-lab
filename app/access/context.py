from dataclasses import dataclass
from typing import Literal


PrincipalKind = Literal[
    "user",
    "service",
]

OrganizationRole = Literal[
    "owner",
    "admin",
    "member",
    "service",
]

DataClassification = Literal[
    "public",
    "internal",
    "confidential",
]


class PrincipalContextError(ValueError):
    pass


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
class PrincipalContext:
    principal_id: int
    organization_id: int
    organization_slug: str
    principal_kind: PrincipalKind
    role: OrganizationRole
    max_classification: DataClassification

    def __post_init__(self) -> None:
        if self.principal_id < 1:
            raise PrincipalContextError(
                "principal_id must be a positive integer."
            )

        if self.organization_id < 1:
            raise PrincipalContextError(
                "organization_id must be a positive integer."
            )

        normalized_slug = (
            self.organization_slug.strip()
        )

        if not normalized_slug:
            raise PrincipalContextError(
                "organization_slug must not be empty."
            )

        if self.principal_kind not in {
            "user",
            "service",
        }:
            raise PrincipalContextError(
                "Invalid principal kind."
            )

        if self.role not in {
            "owner",
            "admin",
            "member",
            "service",
        }:
            raise PrincipalContextError(
                "Invalid organization role."
            )

        if self.max_classification not in {
            "public",
            "internal",
            "confidential",
        }:
            raise PrincipalContextError(
                "Invalid maximum classification."
            )

        object.__setattr__(
            self,
            "organization_slug",
            normalized_slug,
        )

    @property
    def allowed_classifications(
        self,
    ) -> frozenset[str]:
        return _CLASSIFICATION_ACCESS[
            self.max_classification
        ]