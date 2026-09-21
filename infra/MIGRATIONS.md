# Database migrations

## Baseline

PostgreSQL bootstrap scripts `001` through `006` are used only by
`docker-entrypoint-initdb.d` when PostgreSQL initializes a brand-new data
directory.

They must never be rerun by the application migration runner.

The runtime migration system verifies the resulting schema and then records
versions `1` through `6` in `schema_migrations` without executing those
historical scripts.

## Commands

Read-only baseline verification:

    python -m app.db.migrations verify

Register the verified `001` through `006` baseline:

    python -m app.db.migrations baseline

Show migration state:

    python -m app.db.migrations status

Register the baseline if necessary and apply pending migrations:

    python -m app.db.migrations apply

## Production deployment ordering

Start database dependencies first:

    docker compose --env-file /etc/ai-enterprise-lab/production.env -f infra/compose.prod.yaml up -d postgres

Run migrations explicitly using the same application image and environment:

    docker compose --env-file /etc/ai-enterprise-lab/production.env -f infra/compose.prod.yaml run --rm --no-deps app python -m app.db.migrations apply

Only after migration success start or update the application-facing services:

    docker compose --env-file /etc/ai-enterprise-lab/production.env -f infra/compose.prod.yaml up -d redis app caddy n8n

The normal application `CMD` never runs database migrations.

## Concurrency and integrity

The migration command uses a PostgreSQL advisory lock so only one runner can
mutate migration state at a time.

Migration files are versioned, ordered and checksum-verified.

A changed or missing already-applied migration fails closed.

## Rollback

There is no automatic destructive schema downgrade.

Application rollback and database schema rollback are separate operations.
Future schema changes should follow expand/contract practices whenever
possible.
