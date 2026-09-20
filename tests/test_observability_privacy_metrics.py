from app.main import app
from app.observability.metrics import (
    FORBIDDEN_METRIC_LABELS,
    METRIC_LABELS,
)
from app.observability.middleware import (
    UNKNOWN_HTTP_METHOD_LABEL,
    http_method_label,
)


def test_http_method_label_accepts_known_methods():
    assert http_method_label("GET") == "GET"
    assert http_method_label("post") == "POST"
    assert http_method_label("PATCH") == "PATCH"


def test_http_method_label_collapses_arbitrary_values():
    assert (
        http_method_label(
            "X_PRIVATE_METHOD"
        )
        == UNKNOWN_HTTP_METHOD_LABEL
    )

    assert (
        http_method_label(
            "WALDIR_CUSTOM_123"
        )
        == UNKNOWN_HTTP_METHOD_LABEL
    )

    assert (
        http_method_label(None)
        == UNKNOWN_HTTP_METHOD_LABEL
    )


def test_sensitive_metric_labels_are_forbidden():
    expected = {
        "request_id",
        "organization_id",
        "principal_id",
        "document_id",
        "question",
        "prompt",
        "context",
        "credential",
        "secret",
        "response",
        "source_uri",
        "metadata",
        "api_key",
        "authorization",
        "raw_path",
        "exception",
    }

    assert expected <= FORBIDDEN_METRIC_LABELS


def test_metric_contract_avoids_sensitive_labels():
    for labels in METRIC_LABELS.values():
        assert (
            set(labels)
            .isdisjoint(
                FORBIDDEN_METRIC_LABELS
            )
        )


def test_metrics_endpoint_is_not_publicly_exposed():
    paths = {
        getattr(
            route,
            "path",
            None,
        )
        for route in app.routes
    }

    assert "/metrics" not in paths
