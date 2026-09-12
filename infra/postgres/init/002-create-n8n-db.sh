#!/bin/bash
set -euo pipefail

psql \
  --username "$POSTGRES_USER" \
  --dbname "$POSTGRES_DB" \
  --set=n8n_user="$N8N_DB_USER" \
  --set=n8n_password="$N8N_DB_PASSWORD" \
  --set=n8n_database="$N8N_DB_NAME" <<'EOSQL'

SELECT format(
  'CREATE ROLE %I LOGIN PASSWORD %L',
  :'n8n_user',
  :'n8n_password'
)
WHERE NOT EXISTS (
  SELECT 1
  FROM pg_roles
  WHERE rolname = :'n8n_user'
)
\gexec

SELECT format(
  'CREATE DATABASE %I OWNER %I',
  :'n8n_database',
  :'n8n_user'
)
WHERE NOT EXISTS (
  SELECT 1
  FROM pg_database
  WHERE datname = :'n8n_database'
)
\gexec

EOSQL