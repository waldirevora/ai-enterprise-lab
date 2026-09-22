# Quick Start

Este guia leva uma instalação local do AI Enterprise Lab do clone até a primeira consulta RAG autenticada e a primeira execução de agente.

## 1. Pré-requisitos

- Python 3.12
- Git
- Docker
- Docker Compose v2
- Ollama

Este fluxo é destinado ao ambiente local de desenvolvimento. Para produção, use a documentação em `infra/`.

## 2. Clone o repositório

```bash
git clone https://github.com/waldirevora/ai-enterprise-lab.git
cd ai-enterprise-lab
```

## 3. Crie o ambiente Python

```bash
python3.12 -m venv .venv
.venv/bin/python -m pip install --upgrade pip
.venv/bin/python -m pip install -r requirements-runtime.lock.txt
```

Para desenvolvimento e execução da suíte de testes:

```bash
.venv/bin/python -m pip install -r requirements-dev.lock.txt
```

## 4. Configure o ambiente

Crie o arquivo local a partir do template:

```bash
cp .env.example .env
chmod 600 .env
```

Edite `.env` e configure pelo menos os secrets locais usados pelos serviços:

```text
POSTGRES_PASSWORD=
REDIS_PASSWORD=
N8N_DB_PASSWORD=
N8N_ENCRYPTION_KEY=
```

Não faça commit do arquivo `.env`.

As configurações padrão usam:

```text
AI_DEFAULT_PROVIDER=local_fast
AI_LOCAL_FAST_MODEL=qwen2.5-coder:3b
AI_LOCAL_DEEP_MODEL=qwen2.5-coder:7b-instruct-q3_K_S
AI_EMBEDDING_MODEL=qwen3-embedding:0.6b
AI_DEFAULT_ORGANIZATION_SLUG=lab-default
```

## 5. Prepare os modelos locais

Com o Ollama instalado e em execução:

```bash
ollama pull qwen2.5-coder:3b
ollama pull qwen2.5-coder:7b-instruct-q3_K_S
ollama pull qwen3-embedding:0.6b
```

## 6. Inicie a infraestrutura local

```bash
docker compose --env-file .env -f infra/compose.yaml up -d
```

Confira os containers:

```bash
docker compose --env-file .env -f infra/compose.yaml ps
```

## 7. Prepare o banco

Para uma instalação local, use o migration runner da aplicação:

```bash
.venv/bin/python -m app.db.migrations apply
.venv/bin/python -m app.db.migrations status
```

Os scripts históricos `001` a `006` pertencem ao bootstrap de um volume PostgreSQL novo e não devem ser executados manualmente pelo migration runner.

## 8. Inicie a API

Em um terminal separado:

```bash
.venv/bin/uvicorn app.main:app --host 127.0.0.1 --port 8000 --no-access-log
```

Valide health e readiness:

```bash
curl http://127.0.0.1:8000/health
curl http://127.0.0.1:8000/ready
```

Respostas esperadas:

```json
{"status":"ok"}
```

```json
{"status":"ready"}
```

## 9. Crie a primeira credencial

O bootstrap cria ou reutiliza a organização, cria o principal, associa o membership e gera uma API key.

Use um arquivo temporário protegido para capturar a saída:

```bash
umask 077
BOOTSTRAP_OUT="$(mktemp)"

.venv/bin/python -m app.cli.bootstrap_access \
  --organization-slug lab-default \
  --organization-name "AI Enterprise Lab" \
  --display-name "Local Owner" \
  --subject local-owner \
  --role owner \
  --max-classification internal \
  --credential-name quickstart \
  > "$BOOTSTRAP_OUT"

export AEL_API_KEY="$(sed -n 's/^api_key=//p' "$BOOTSTRAP_OUT")"

grep -v "^api_key=" "$BOOTSTRAP_OUT"
rm -f "$BOOTSTRAP_OUT"

test -n "$AEL_API_KEY" && echo "AEL_API_KEY loaded"
```

A API key é um segredo. Não a salve no Git, README, logs ou arquivos públicos.

As APIs autenticadas usam:

```text
Authorization: Bearer <API_KEY>
```

## 10. Ingira o primeiro documento

Crie um pequeno documento de teste:

```bash
printf "%s\n" \
  "AI Enterprise Lab is a private enterprise AI architecture." \
  "The platform integrates RAG, access control, agents and local models." \
  > /tmp/ael-quickstart.txt
```

Faça a ingestão autenticada:

```bash
AEL_API_KEY="$AEL_API_KEY" \
.venv/bin/python -m app.cli.ingest_document \
  --file /tmp/ael-quickstart.txt \
  --title "Quick Start Document" \
  --source quickstart \
  --classification internal
```

Uma ingestão bem-sucedida retorna um resumo semelhante a:

```text
INGEST_DOCUMENT=PASS
document_id=<id>
chunks_inserted=<n>
duplicate=false
```

## 11. Faça a primeira consulta RAG autenticada

Com a API ainda em execução:

```bash
curl -sS -X POST \
  http://127.0.0.1:8000/v1/rag/generate-authenticated \
  -H "Authorization: Bearer $AEL_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "question": "What capabilities are described in the Quick Start Document?"
  }'
```

A resposta inclui a resposta gerada, provider/model utilizados, classificação efetiva e citations dos chunks autorizados.

## 12. Execute o primeiro agente

O agente Enterprise Knowledge usa o contexto autenticado e somente o conhecimento autorizado para o principal.

```bash
curl -sS -X POST \
  http://127.0.0.1:8000/v1/agents/enterprise-knowledge/run \
  -H "Authorization: Bearer $AEL_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "message": "Summarize what the Quick Start Document says about the platform."
  }'
```

A resposta do agente pode incluir `citations`, `tool_trace`, `steps_executed` e métricas da geração.

## 13. Verificações úteis

Provider catalog:

```bash
curl http://127.0.0.1:8000/v1/providers
```

Migration status:

```bash
.venv/bin/python -m app.db.migrations status
```

Testes:

```bash
.venv/bin/python -m pytest -q
```

## 14. Encerramento local

Para parar os serviços Docker sem remover os volumes:

```bash
docker compose --env-file .env -f infra/compose.yaml stop
```

Para iniciar novamente:

```bash
docker compose --env-file .env -f infra/compose.yaml start
```

## Segurança

Não exponha `.env`, API keys, senhas, tokens ou outputs contendo secrets.

Não use `docker compose down -v` em ambientes com dados que precisam ser preservados.

APIs autenticadas derivam organização, principal, role, classificação e escopo a partir da credencial. O cliente não escolhe arbitrariamente esses limites.

## Próximos documentos

Depois deste Quick Start, consulte os guias de uso, agentes/tools, troubleshooting e operação de produção.
