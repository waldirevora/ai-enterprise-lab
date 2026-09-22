# Troubleshooting

**Language:** [Português (Brasil)](TROUBLESHOOTING.md) | English

## 1. `/ready` is not ready

```bash
docker compose --env-file .env -f infra/compose.yaml ps
.venv/bin/python -m app.db.migrations status
```

Check PostgreSQL and Redis before debugging the AI layer.

## 2. PostgreSQL password is not configured

Set `POSTGRES_PASSWORD` in `.env`. Do not publish the value in logs or issues.

## 3. Docker Compose fails

```bash
docker compose --env-file .env -f infra/compose.yaml config --quiet
docker compose --env-file .env -f infra/compose.yaml ps
```

## 4. Ollama or a model is unavailable

```bash
ollama list
ollama pull qwen2.5-coder:3b
ollama pull qwen2.5-coder:7b-instruct-q3_K_S
ollama pull qwen3-embedding:0.6b
```

## 5. HTTP 401

Authenticated endpoints require `Authorization: Bearer <API_KEY>`.

Missing, malformed, expired or revoked credentials are rejected.

## 6. `AEL_API_KEY is not configured`

```bash
export AEL_API_KEY="<API_KEY>"
```

Never place the API key in a URL.

## 7. Classification exceeds credential scope

Use a classification authorized by the credential. Do not attempt to bypass server-side authorization.

## 8. Duplicate document

`duplicate=true` with `chunks_inserted=0` means the content already exists in the ingestion deduplication scope.

## 9. Migration inconsistency

```bash
.venv/bin/python -m app.db.migrations verify
.venv/bin/python -m app.db.migrations status
.venv/bin/python -m app.db.migrations apply
```

Do not manually replay historical bootstrap scripts `001` through `006` over an initialized database.

## 10. Bootstrap blocked in production

This is intentional. `bootstrap_access` fails closed when `APP_ENV=production`.

## 11. Revoke a credential

```bash
AEL_API_KEY="$AEL_API_KEY" \
.venv/bin/python -m app.cli.revoke_api_key
```

A revoked credential cannot be reactivated by the client. Create a new authorized credential when required.

## 12. Before reporting a problem

Include the failing step, sanitized error, environment and return code. Remove credentials, `.env` values and private enterprise data.

See [SECURITY.md](../../SECURITY.md) for vulnerability reporting.
