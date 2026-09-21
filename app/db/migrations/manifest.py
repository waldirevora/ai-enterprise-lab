from dataclasses import dataclass


@dataclass(frozen=True)
class BaselineMigration:
    version: int
    name: str
    checksum_sha256: str


BASELINE_MIGRATIONS = (
    BaselineMigration(
        1,
        "001-enable-vector.sql",
        "a183b9e16fc492735db807b4c73d765c12b07b330987caa5e65c3eca71bacc16",
    ),
    BaselineMigration(
        2,
        "002-create-n8n-db.sh",
        "bef31e519fe8ead7e7d6c08493ba4d9cba288a25b6c5f747181adc7d7f20d0f2",
    ),
    BaselineMigration(
        3,
        "003-create-rag-schema.sql",
        "45bc1eddd382889152e7e3287e57384095446aa6719bb8abbd40d78ff18b9d37",
    ),
    BaselineMigration(
        4,
        "004-create-access-control-schema.sql",
        "d35187e8b173790451b684d46bd292b7747e6079c959a60284dc50f2c966d5e2",
    ),
    BaselineMigration(
        5,
        "005-create-organizational-units-schema.sql",
        "7a84092dd741480a0bf10e605f7edcf2775dae07c578c4b6101db120778a13ba",
    ),
    BaselineMigration(
        6,
        "006-create-document-acl-schema.sql",
        "9989ab88d5e984512b9e69878bffcdc34cb6ac71caeae87fa666d79deaec04b1",
    ),
)


BASELINE_MAX_VERSION = 6
