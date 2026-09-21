# Rollback and Recovery

## Scope

This runbook covers:

- application rollback;
- PostgreSQL logical backup;
- recovery of the AI Enterprise Lab database;
- recovery of the n8n database;
- migration-related recovery boundaries.

Redis is not a durable data store in this deployment and is not part of the
backup set.

Caddy certificates can normally be reissued. The persistent Caddy volume
should still be preserved during ordinary deployments, but it is not the
primary business-data backup.

## Application rollback

Production images must use immutable release tags.

Recommended examples:

    git-<commit-sha>

or another release identifier that is never reused.

Before deployment, record the currently running image tag.

Routine application rollback means selecting the previous known-good
`APP_IMAGE_TAG` and recreating the application container.

Example:

    docker compose \
      --env-file /etc/ai-enterprise-lab/production.env \
      -f infra/compose.prod.yaml \
      up -d --no-deps app

Then validate:

    /health
    /ready

Caddy normally does not need to be rolled back when only the application image
changes.

## Database rollback policy

Database migrations do not have automatic destructive down migrations.

Routine application rollback must rely on expand/contract schema evolution so
the previous application version remains compatible with the current schema.

Restoring a database backup is a recovery operation, not the default response
to an application deployment failure.

If a migration causes destructive or unrecoverable data/schema damage:

1. stop writers;
2. preserve the failed database state for investigation;
3. select the correct pre-migration backup;
4. restore into an isolated environment first when time permits;
5. perform the controlled production restore;
6. validate migration metadata, health and readiness;
7. only then reopen traffic.

## Backup set

A production backup set contains:

    app.dump
    n8n.dump
    SHA256SUMS
    MANIFEST.txt

The application and n8n dumps should be created in the same backup operation.

The backup directory and files are sensitive and must not be stored in Git.

Recommended permissions:

    directory: 0700
    files:     0600

## Backup command

Use the versioned helper:

    infra/scripts/backup_postgres.sh \
      infra/compose.prod.yaml \
      /etc/ai-enterprise-lab/production.env \
      /var/backups/ai-enterprise-lab/<timestamp>

The script does not print database passwords.

It creates PostgreSQL custom-format dumps and verifies that both archives can
be read by `pg_restore`.

## n8n encryption key

`N8N_ENCRYPTION_KEY` is critical recovery material.

The database dump alone is not sufficient to recover encrypted n8n
credentials if this key is lost.

The production encryption key must therefore be preserved separately in the
approved secret-management / encrypted recovery process.

It must not be stored inside the repository or ordinary database backup
directory.

## Restore model

A disaster-recovery PostgreSQL instance should first be initialized with the
current deployment environment and the bootstrap scripts.

That recreates:

- the main PostgreSQL role/database;
- the n8n role/database;
- required PostgreSQL extension/bootstrap objects.

Then restore the logical archives with:

    pg_restore \
      --exit-on-error \
      --clean \
      --if-exists \
      --no-owner \
      --no-privileges \
      -d <database> \
      <archive>

The exact production restore must be executed only during an approved recovery
operation because `--clean` is destructive to the target database.

## Migration metadata after restore

The application database backup includes `schema_migrations`.

After restore run:

    python -m app.db.migrations status

The command must report:

    baseline_schema: valid
    baseline_registration: valid

Any checksum mismatch or incomplete migration history is a recovery blocker.

## Recovery validation

Before reopening traffic validate:

    PostgreSQL reachable
    migration status valid
    /health returns 200
    /ready returns 200
    n8n starts with the original N8N_ENCRYPTION_KEY
    application logs contain no startup/database errors

## Backup retention

Retention duration is an operational/business decision and is not fixed by the
application code.

At minimum, do not delete the pre-deployment backup until the new deployment
and its migration state have been validated.

## Recovery principle

Application rollback and schema/data recovery are separate operations.

Prefer:

    immutable application rollback
    +
    forward-compatible database schema

over destructive database restoration whenever possible.
