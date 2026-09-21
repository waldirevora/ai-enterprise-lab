#!/usr/bin/env bash

set -euo pipefail

if [ "$#" -ne 3 ]; then
    echo "Usage: $0 <compose-file> <env-file> <backup-dir>" >&2
    exit 2
fi

COMPOSE_FILE="$1"
ENV_FILE="$2"
BACKUP_DIR="$3"

umask 077

mkdir -p "$BACKUP_DIR"
chmod 700 "$BACKUP_DIR"

POSTGRES_ID="$(
    docker compose \
        --env-file "$ENV_FILE" \
        -f "$COMPOSE_FILE" \
        ps -q postgres
)"

if [ -z "$POSTGRES_ID" ]; then
    echo "PostgreSQL container not found." >&2
    exit 1
fi

if ! docker inspect \
    "$POSTGRES_ID" \
    >/dev/null 2>&1
then
    echo "PostgreSQL container is unavailable." >&2
    exit 1
fi

APP_DUMP="$BACKUP_DIR/app.dump"
N8N_DUMP="$BACKUP_DIR/n8n.dump"
CHECKSUMS="$BACKUP_DIR/SHA256SUMS"
MANIFEST="$BACKUP_DIR/MANIFEST.txt"

docker exec \
    "$POSTGRES_ID" \
    sh -lc '
        exec pg_dump \
            -U "$POSTGRES_USER" \
            -d "$POSTGRES_DB" \
            -Fc
    ' \
    > "$APP_DUMP"

docker exec \
    "$POSTGRES_ID" \
    sh -lc '
        exec pg_dump \
            -U "$POSTGRES_USER" \
            -d "$N8N_DB_NAME" \
            -Fc
    ' \
    > "$N8N_DUMP"

chmod 600 \
    "$APP_DUMP" \
    "$N8N_DUMP"

docker exec -i     "$POSTGRES_ID"     pg_restore -l     < "$APP_DUMP"     >/dev/null

docker exec -i     "$POSTGRES_ID"     pg_restore -l     < "$N8N_DUMP"     >/dev/null

(
    cd "$BACKUP_DIR"

    sha256sum \
        app.dump \
        n8n.dump \
        > SHA256SUMS
)

chmod 600 "$CHECKSUMS"

GIT_COMMIT="$(
    git rev-parse HEAD \
        2>/dev/null \
        || printf 'unknown'
)"

POSTGRES_IMAGE="$(
    docker inspect \
        "$POSTGRES_ID" \
        --format '{{.Config.Image}}'
)"

cat > "$MANIFEST" <<EOF
format=ai-enterprise-lab-postgres-backup-v1
git_commit=$GIT_COMMIT
postgres_image=$POSTGRES_IMAGE
app_dump=app.dump
n8n_dump=n8n.dump
checksums=SHA256SUMS
EOF

chmod 600 "$MANIFEST"

echo "backup_status=ok"
echo "backup_dir=$BACKUP_DIR"
echo "app_archive=valid"
echo "n8n_archive=valid"
