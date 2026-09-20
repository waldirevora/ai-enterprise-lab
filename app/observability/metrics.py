from prometheus_client import (
    CollectorRegistry,
    Counter,
    Histogram,
)


METRICS_REGISTRY = CollectorRegistry(
    auto_describe=True,
)


REQUEST_DURATION_BUCKETS = (
    0.01,
    0.025,
    0.05,
    0.1,
    0.25,
    0.5,
    1.0,
    2.5,
    5.0,
    10.0,
    30.0,
    60.0,
)


RAG_CHUNK_BUCKETS = (
    0,
    1,
    2,
    3,
    5,
    10,
)


HTTP_REQUESTS_TOTAL = Counter(
    "ai_enterprise_http_requests_total",
    "Total number of HTTP requests.",
    (
        "method",
        "route",
        "status_class",
    ),
    registry=METRICS_REGISTRY,
)


HTTP_REQUEST_DURATION_SECONDS = Histogram(
    "ai_enterprise_http_request_duration_seconds",
    "HTTP request duration in seconds.",
    (
        "method",
        "route",
    ),
    buckets=REQUEST_DURATION_BUCKETS,
    registry=METRICS_REGISTRY,
)


GENERATION_REQUESTS_TOTAL = Counter(
    "ai_enterprise_generation_requests_total",
    "Total number of generation requests.",
    (
        "provider",
        "backend",
        "outcome",
    ),
    registry=METRICS_REGISTRY,
)


GENERATION_DURATION_SECONDS = Histogram(
    "ai_enterprise_generation_duration_seconds",
    "Generation duration in seconds.",
    (
        "provider",
        "backend",
    ),
    buckets=REQUEST_DURATION_BUCKETS,
    registry=METRICS_REGISTRY,
)


RAG_REQUESTS_TOTAL = Counter(
    "ai_enterprise_rag_requests_total",
    "Total number of RAG requests.",
    (
        "outcome",
    ),
    registry=METRICS_REGISTRY,
)


RAG_RETRIEVAL_DURATION_SECONDS = Histogram(
    "ai_enterprise_rag_retrieval_duration_seconds",
    "RAG retrieval duration in seconds.",
    (
        "outcome",
    ),
    buckets=REQUEST_DURATION_BUCKETS,
    registry=METRICS_REGISTRY,
)


RAG_CHUNKS_USED = Histogram(
    "ai_enterprise_rag_chunks_used",
    "Number of RAG chunks used per request.",
    (
        "outcome",
    ),
    buckets=RAG_CHUNK_BUCKETS,
    registry=METRICS_REGISTRY,
)


AGENT_RUNS_TOTAL = Counter(
    "ai_enterprise_agent_runs_total",
    "Total number of agent runs.",
    (
        "outcome",
    ),
    registry=METRICS_REGISTRY,
)


AGENT_RUN_DURATION_SECONDS = Histogram(
    "ai_enterprise_agent_run_duration_seconds",
    "Agent run duration in seconds.",
    (
        "outcome",
    ),
    buckets=REQUEST_DURATION_BUCKETS,
    registry=METRICS_REGISTRY,
)


TOKENS_TOTAL = Counter(
    "ai_enterprise_tokens_total",
    "Total number of model tokens processed.",
    (
        "provider",
        "token_type",
    ),
    registry=METRICS_REGISTRY,
)


ESTIMATED_EXTERNAL_COST_USD_TOTAL = Counter(
    "ai_enterprise_estimated_external_cost_usd_total",
    "Estimated external provider cost in USD.",
    (
        "provider",
        "pricing_tier",
    ),
    registry=METRICS_REGISTRY,
)


RATE_LIMIT_EVENTS_TOTAL = Counter(
    "ai_enterprise_rate_limit_events_total",
    "Total number of rate-limit events.",
    (
        "outcome",
    ),
    registry=METRICS_REGISTRY,
)


METRIC_LABELS = {
    "http_requests": (
        "method",
        "route",
        "status_class",
    ),
    "http_duration": (
        "method",
        "route",
    ),
    "generation_requests": (
        "provider",
        "backend",
        "outcome",
    ),
    "generation_duration": (
        "provider",
        "backend",
    ),
    "rag_requests": (
        "outcome",
    ),
    "rag_retrieval_duration": (
        "outcome",
    ),
    "rag_chunks_used": (
        "outcome",
    ),
    "agent_runs": (
        "outcome",
    ),
    "agent_run_duration": (
        "outcome",
    ),
    "tokens": (
        "provider",
        "token_type",
    ),
    "estimated_external_cost": (
        "provider",
        "pricing_tier",
    ),
    "rate_limit_events": (
        "outcome",
    ),
}


FORBIDDEN_METRIC_LABELS = frozenset(
    {
        "request_id",
        "organization_id",
        "principal_id",
        "document_id",
        "question",
        "prompt",
        "context",
        "credential",
        "secret",
        "exception",
        "raw_path",
        "authorization",
        "api_key",
        "metadata",
        "source_uri",
        "response",
    }
)


def http_status_class(
    status_code: int,
) -> str:
    if 100 <= status_code <= 599:
        return f"{status_code // 100}xx"

    return "unknown"
