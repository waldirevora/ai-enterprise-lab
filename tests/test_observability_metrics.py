from prometheus_client import generate_latest

from app.observability.metrics import (
    FORBIDDEN_METRIC_LABELS,
    HTTP_REQUESTS_TOTAL,
    METRIC_LABELS,
    METRICS_REGISTRY,
    http_status_class,
)


def test_metrics_use_custom_registry_without_default_collectors():
    payload = generate_latest(
        METRICS_REGISTRY
    ).decode()

    assert "python_gc_" not in payload
    assert "python_info" not in payload
    assert "process_" not in payload


def test_http_request_metric_is_exposed():
    HTTP_REQUESTS_TOTAL.labels(
        method="GET",
        route="/health",
        status_class="2xx",
    ).inc()

    payload = generate_latest(
        METRICS_REGISTRY
    ).decode()

    assert (
        "ai_enterprise_http_requests_total"
        in payload
    )

    assert 'method="GET"' in payload
    assert 'route="/health"' in payload
    assert 'status_class="2xx"' in payload


def test_metric_contract_has_no_sensitive_labels():
    labels = {
        label
        for metric_labels in (
            METRIC_LABELS.values()
        )
        for label in metric_labels
    }

    assert labels.isdisjoint(
        FORBIDDEN_METRIC_LABELS
    )


def test_http_status_class_is_bounded():
    assert http_status_class(200) == "2xx"
    assert http_status_class(404) == "4xx"
    assert http_status_class(503) == "5xx"


def test_invalid_http_status_class_is_unknown():
    assert http_status_class(0) == "unknown"
    assert http_status_class(999) == "unknown"
