from app.rag.retrieval import (
    _build_acl_filter,
)


def test_public_acl_filter_allows_only_inherited():
    sql, params = _build_acl_filter(
        principal_id=None,
    )

    assert (
        sql
        == "d.access_mode = 'inherited'"
    )

    assert params == []


def test_authenticated_acl_filter_supports_restricted():
    sql, params = _build_acl_filter(
        principal_id=77,
    )

    assert (
        "d.access_mode = 'inherited'"
        in sql
    )

    assert (
        "d.access_mode = 'restricted'"
        in sql
    )

    assert (
        "rag_document_acl_entries"
        in sql
    )

    assert (
        "a.organization_id"
        in sql
    )

    assert (
        "a.document_id"
        in sql
    )

    assert (
        "a.principal_id"
        in sql
    )

    assert (
        "a.permission"
        in sql
    )

    assert (
        "'read'"
        in sql
    )

    assert (
        "a.status"
        in sql
    )

    assert (
        "'active'"
        in sql
    )

    assert params == [
        77,
    ]