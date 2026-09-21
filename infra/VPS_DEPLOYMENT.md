# Manual VPS Deployment

## Purpose

This runbook defines the first production deployment and manual update process
for AI Enterprise Lab.

The deployment remains manual in FASE 29.

Continuous deployment is explicitly deferred to the next phase.

## Production topology

Traffic path:

    Internet
      -> Caddy :80/:443
      -> FastAPI app :8000 internal
      -> PostgreSQL / Redis internal

n8n remains available only through:

    127.0.0.1:5678

Do not publish:

    PostgreSQL 5432
    Redis 6379
    FastAPI 8000

Caddy is the only public ingress.

## Host prerequisites

The VPS must provide:

    Docker Engine
    Docker Compose v2
    Git
    outbound internet access
    persistent disk for Docker volumes

The operator must have authorized Docker access.

Do not expose the Docker API publicly.

## DNS

Before requesting the first public TLS certificate:

- create the required DNS A record for `APP_DOMAIN`;
- add an AAAA record only when IPv6 is correctly configured;
- wait until the hostname resolves to the VPS;
- confirm TCP ports 80 and 443 are externally reachable.

Caddy uses public ACME issuance for the real production hostname.

UDP 443 is optional for HTTP/3 and is not required for certificate issuance.

## Firewall

Allow only the ports required by the deployment.

Typical public ingress:

    SSH administration port
    TCP 80
    TCP 443
    UDP 443 optional

Do not expose publicly:

    5432
    6379
    8000
    5678

n8n binds only to loopback.

## Repository

Recommended deployment directory:

    /opt/ai-enterprise-lab

Checkout the exact commit intended for the release.

Confirm:

    git status
    git rev-parse HEAD

Do not deploy from a dirty working tree.

## Production secrets

The real production environment file must remain outside the repository.

Recommended path:

    /etc/ai-enterprise-lab/production.env

Required permissions:

    0600

Follow:

    infra/PRODUCTION_ENV.md

Never print the complete environment file.

## Immutable application tag

Each deployment must use a new immutable image tag.

Recommended convention:

    git-<commit-sha>

Example:

    git-a1b2c3d4e5f6

Set that exact value in:

    APP_IMAGE_TAG

Do not use:

    latest
    prod
    production
    main
    master
    dev
    staging

Do not reuse a tag after it has been deployed.

## Preflight

Run:

    infra/scripts/preflight_vps.sh \
      infra/compose.prod.yaml \
      /etc/ai-enterprise-lab/production.env

Resolve every `preflight_error` before deployment.

If a configured Docker subnet already appears in the host routing table,
investigate the conflict before the first deployment.

The production networks currently reserve:

    172.30.10.0/24
    172.30.20.0/24

## Build release image

Validate the source tree first:

    git status --short

The deployment working tree must be clean.

Build using the production environment so the compose image name receives the
immutable release tag:

    docker compose \
      --env-file /etc/ai-enterprise-lab/production.env \
      -f infra/compose.prod.yaml \
      build app

Confirm the image exists:

    docker image ls ai-enterprise-lab

## Existing deployment backup

For an update to an existing deployment, create a backup before migrations.

Example backup directory:

    /var/backups/ai-enterprise-lab/<timestamp>

Run:

    infra/scripts/backup_postgres.sh \
      infra/compose.prod.yaml \
      /etc/ai-enterprise-lab/production.env \
      /var/backups/ai-enterprise-lab/<timestamp>

Do not delete the previous known-good backup until the new release is fully
validated.

For a first deployment with no existing PostgreSQL volume, this backup step
does not apply.

## Start PostgreSQL

Start only PostgreSQL first:

    docker compose \
      --env-file /etc/ai-enterprise-lab/production.env \
      -f infra/compose.prod.yaml \
      up -d postgres

Wait until it is healthy:

    docker compose \
      --env-file /etc/ai-enterprise-lab/production.env \
      -f infra/compose.prod.yaml \
      ps postgres

Do not proceed while PostgreSQL is unhealthy.

## Database migration

Migrations are an explicit deployment operation.

They are not executed by the FastAPI startup command.

Run:

    docker compose \
      --env-file /etc/ai-enterprise-lab/production.env \
      -f infra/compose.prod.yaml \
      run --rm --no-deps app \
      python -m app.db.migrations apply

Expected behavior:

    baseline schema verified
    migration metadata valid
    pending migrations applied once
    exit code 0

Any migration error blocks the deployment.

Do not start the new application release after a failed migration.

## Start application stack

After migration success:

    docker compose \
      --env-file /etc/ai-enterprise-lab/production.env \
      -f infra/compose.prod.yaml \
      up -d redis app caddy n8n

Check:

    docker compose \
      --env-file /etc/ai-enterprise-lab/production.env \
      -f infra/compose.prod.yaml \
      ps

Expected:

    postgres healthy
    redis healthy
    app healthy
    caddy running
    n8n running/ready

## HTTPS validation

Validate liveness through the real public hostname:

    curl -fsS https://<APP_DOMAIN>/health

Validate readiness:

    curl -fsS https://<APP_DOMAIN>/ready

Both must return HTTP 200 before the deployment is accepted.

Verify HTTPS/TLS:

    curl -Iv https://<APP_DOMAIN>/

The real production validation belongs to D11 and must verify the issued public
certificate rather than Caddy's local internal CA.

## Port exposure

Verify host listeners after startup.

Public:

    80
    443

Loopback only:

    5678

Must not be public:

    5432
    6379
    8000

Container-level PostgreSQL, Redis and application traffic remains on Docker
networks.

## Migration status

After deployment:

    docker compose \
      --env-file /etc/ai-enterprise-lab/production.env \
      -f infra/compose.prod.yaml \
      exec -T app \
      python -m app.db.migrations status

Expected:

    baseline_schema: valid
    baseline_registration: valid
    future_migrations_pending: 0

## Logs

Review startup logs without exposing secrets:

    docker compose \
      --env-file /etc/ai-enterprise-lab/production.env \
      -f infra/compose.prod.yaml \
      logs --tail 100 app caddy postgres redis n8n

Do not paste environment dumps or `docker inspect` environment output into
shared troubleshooting channels.

## Application rollback

If the application release fails but the database remains compatible:

1. set `APP_IMAGE_TAG` to the previous known-good immutable release tag;
2. recreate only the application;
3. validate health and readiness.

Command:

    docker compose \
      --env-file /etc/ai-enterprise-lab/production.env \
      -f infra/compose.prod.yaml \
      up -d --no-deps app

Then verify:

    /health
    /ready

Do not automatically roll back database migrations.

For database/data recovery follow:

    infra/ROLLBACK_RECOVERY.md

## Deployment acceptance gate

A release is accepted only when all of the following are true:

    compose configuration valid
    PostgreSQL healthy
    migration command successful
    migration status clean
    Redis healthy
    application healthy
    public /health = 200
    public /ready = 200
    HTTPS certificate valid
    only intended host ports exposed
    n8n loopback-only
    no startup errors requiring rollback

Keep the previous image and pre-deployment backup until this gate passes.
