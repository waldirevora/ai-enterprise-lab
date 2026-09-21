#!/usr/bin/env bash

set -euo pipefail

MODE="full"

if [ "${1:-}" = "--contract-only" ]; then
    MODE="contract-only"
    shift
fi

if [ "$#" -ne 2 ]; then
    echo "Usage: $0 [--contract-only] <compose-file> <env-file>" >&2
    exit 2
fi

COMPOSE_FILE="$1"
ENV_FILE="$2"

fail() {
    echo "preflight_error: $*" >&2
    exit 1
}

env_value() {
    local key="$1"
    local line=""
    local value=""

    line="$(
        grep -m 1 -E \
            "^[[:space:]]*${key}[[:space:]]*=" \
            "$ENV_FILE" \
            || true
    )"

    if [ -z "$line" ]; then
        printf '
'
        return 0
    fi

    value="${line#*=}"

    value="$(
        printf '%s' "$value" \
            | sed \
                -e 's/^[[:space:]]*//' \
                -e 's/[[:space:]]*$//'
    )"

    case "$value" in
        \"*\")
            value="${value#\"}"
            value="${value%\"}"
            ;;
        \'*\')
            value="${value#\'}"
            value="${value%\'}"
            ;;
    esac

    printf '%s
' "$value"
}


[ -f "$COMPOSE_FILE" ] \
    || fail "compose file not found"

[ -f "$ENV_FILE" ] \
    || fail "production env file not found"


ENV_MODE="$(
    stat -c '%a' \
        "$ENV_FILE"
)"

[ "$ENV_MODE" = "600" ] \
    || fail "production env file must use mode 600"


REPO_ROOT="$(
    git rev-parse \
        --show-toplevel
)"

ENV_REAL="$(
    realpath \
        "$ENV_FILE"
)"

case "$ENV_REAL" in
    "$REPO_ROOT"/*)
        fail "production env file must be outside repository"
        ;;
esac


command -v docker \
    >/dev/null 2>&1 \
    || fail "docker command not found"

docker info \
    >/dev/null 2>&1 \
    || fail "Docker Engine is not reachable"

docker compose version \
    >/dev/null 2>&1 \
    || fail "Docker Compose v2 is unavailable"


APP_DOMAIN="$(
    env_value APP_DOMAIN
)"

APP_IMAGE_TAG="$(
    env_value APP_IMAGE_TAG
)"


[ -n "$APP_DOMAIN" ] \
    || fail "APP_DOMAIN is empty"

[ -n "$APP_IMAGE_TAG" ] \
    || fail "APP_IMAGE_TAG is empty"


case "$APP_IMAGE_TAG" in
    latest|prod|production|main|master|dev|development|staging)
        fail "APP_IMAGE_TAG uses a mutable deployment tag"
        ;;
esac


docker compose \
    --env-file "$ENV_FILE" \
    -f "$COMPOSE_FILE" \
    config \
    --quiet \
    || fail "production compose validation failed"


echo "env_permissions=ok"
echo "env_location=outside_repository"
echo "docker_engine=ok"
echo "docker_compose=ok"
echo "compose_contract=ok"
echo "release_tag_contract=ok"


if [ "$MODE" = "contract-only" ]; then
    echo "network_checks=skipped"
    echo "preflight_status=ok"
    exit 0
fi


if command -v getent >/dev/null 2>&1; then
    if getent ahosts \
        "$APP_DOMAIN" \
        >/dev/null 2>&1
    then
        echo "dns_resolution=ok"
    else
        fail "APP_DOMAIN does not resolve"
    fi
else
    echo "dns_resolution=not_checked"
fi


if command -v ip >/dev/null 2>&1; then
    for subnet in \
        172.30.10.0/24 \
        172.30.20.0/24
    do
        if ip route show \
            | awk '{print $1}' \
            | grep -Fxq "$subnet"
        then
            echo "network_route_present=$subnet"
            echo "network_route_review_required=$subnet"
        else
            echo "network_route_available=$subnet"
        fi
    done
fi


if command -v ss >/dev/null 2>&1; then
    for port in 80 443 5678; do
        if ss -ltnH \
            | awk '{print $4}' \
            | grep -Eq "(^|:)$port$"
        then
            echo "listener_present=$port"
        else
            echo "listener_absent=$port"
        fi
    done
fi


echo "preflight_status=ok"
