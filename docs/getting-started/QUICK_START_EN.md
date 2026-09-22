# Quick Start

**Language:** [Português (Brasil)](QUICK_START.md) | English

This guide takes a local AI Enterprise Lab installation from clone to the first authenticated RAG query and agent execution.

## 1. Prerequisites

- Python 3.12
- Git
- Docker
- Docker Compose v2
- Ollama

## 2. Clone and Python environment

```bash
git clone https://github.com/waldirevora/ai-enterprise-lab.git
cd ai-enterprise-lab
python3.12 -m venv .venv
.venv/bin/python -m pip install --upgrade pip
.venv/bin/python -m pip install -r requirements-runtime.lock.txt
```

For development and tests:

```bash
.venv/bin/python -m pip install -r requirements-dev.lock.txt
```

## 3. Environment

```bash
cp .env.example .env
chmod 600 .env
```

Configure the required local secrets in `.env`, including PostgreSQL, Redis and n8n credentials. Never commit `.env`.

## 4. Local models

```bash
ollama pull qwen2.5-coder:3b
ollama pull qwen2.5-coder:7b-instruct-q3_K_S
ollama pull qwen3-embedding:0.6b
```

## 5. Infrastructure and migrations

```bash
docker compose --env-file .env -f infra/compose.yaml up -d
.venv/bin/python -m app.db.migrations apply
.venv/bin/python -m app.db.migrations status
```

## 6. Start the API

```bash
.venv/bin/uvicorn app.main:app --host 127.0.0.1 --port 8000 --no-access-log
```

Verify:

```bash
curl http://127.0.0.1:8000/health
curl http://127.0.0.1:8000/ready
```

## 7. Create the first local credential

```bash
umask 077
BOOTSTRAP_OUT="$(mktemp)"

.venv/bin/python -m app.cli.bootstrap_access \
  --display-name "Local Owner" \
  --subject local-owner \
  --role owner \
  --max-classification internal \
  > "$BOOTSTRAP_OUT"

export AEL_API_KEY="$(sed -n 's/^api_key=//p' "$BOOTSTRAP_OUT")"
grep -v "^api_key=" "$BOOTSTRAP_OUT"
rm -f "$BOOTSTRAP_OUT"
```

`bootstrap_access` is local-development oriented and refuses to run when `APP_ENV=production`.

## 8. Ingest a document

```bash
AEL_API_KEY="$AEL_API_KEY" \
.venv/bin/python -m app.cli.ingest_document \
  --file ./document.txt \
  --title "Internal document" \
  --source quickstart \
  --classification internal
```

## 9. Authenticated RAG

```bash
curl -sS -X POST \
  http://127.0.0.1:8000/v1/rag/generate-authenticated \
  -H "Authorization: Bearer $AEL_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"question":"Summarize the authorized document."}'
```

## 10. Enterprise Knowledge Agent

```bash
curl -sS -X POST \
  http://127.0.0.1:8000/v1/agents/enterprise-knowledge/run \
  -H "Authorization: Bearer $AEL_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"message":"Summarize the authorized enterprise knowledge."}'
```

## 11. Revoke the API key

```bash
AEL_API_KEY="$AEL_API_KEY" \
.venv/bin/python -m app.cli.revoke_api_key
unset AEL_API_KEY
```

## 12. Tests and shutdown

```bash
.venv/bin/python -m pytest -q
docker compose --env-file .env -f infra/compose.yaml stop
```

Do not use destructive volume-removal commands when data must be preserved.

See also [Troubleshooting](TROUBLESHOOTING_EN.md) and the repository [Security Policy](../../SECURITY.md).
