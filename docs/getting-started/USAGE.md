# Guia de Uso

Este documento descreve os fluxos operacionais principais do AI Enterprise Lab depois que o ambiente local já foi configurado.

Para instalação inicial, consulte [Quick Start](QUICK_START.md).

## 1. Fluxo operacional local

Em uma sessão normal de desenvolvimento:

```bash
docker compose --env-file .env -f infra/compose.yaml start

.venv/bin/python -m app.db.migrations status

.venv/bin/uvicorn app.main:app \
  --host 127.0.0.1 \
  --port 8000 \
  --no-access-log
```

Confirme:

```bash
curl http://127.0.0.1:8000/health
curl http://127.0.0.1:8000/ready
```

## 2. Endpoints principais

```text
GET  /health
GET  /ready
GET  /v1/providers
POST /v1/generate
POST /v1/rag/generate
POST /v1/rag/generate-authenticated
POST /v1/agents/enterprise-knowledge/run
```

Em ambiente diferente de produção, FastAPI também disponibiliza `/docs`, `/redoc` e `/openapi.json`.

## 3. Autenticação

Os endpoints autenticados usam API key no header Bearer:

```text
Authorization: Bearer <API_KEY>
```

A organização, o principal, a role e o limite máximo de classificação são derivados da credencial validada no servidor.

Não envie organization ID ou principal ID como mecanismo para ampliar o escopo da credencial.

## 4. Bootstrap de acesso

O CLI `bootstrap_access` permite criar o primeiro acesso local ou uma nova credencial para um principal bootstrap.

```bash
.venv/bin/python -m app.cli.bootstrap_access \
  --display-name "Local Owner" \
  --subject local-owner \
  --role owner \
  --max-classification internal
```

O token completo é mostrado uma vez pela ferramenta. Armazene-o de forma segura.

Executar novamente o bootstrap pode gerar uma nova credencial. Não trate a execução repetida como mecanismo de consulta da chave anterior.

## 5. Carregar a API key na sessão

```bash
export AEL_API_KEY="<API_KEY>"
```

Para confirmar apenas que a variável existe, sem imprimir o segredo:

```bash
test -n "$AEL_API_KEY" && echo "AEL_API_KEY loaded"
```

## 6. Ingestão de documentos

O CLI de ingestão aceita arquivos de texto UTF-8 e autentica o usuário pela variável `AEL_API_KEY`.

```bash
AEL_API_KEY="$AEL_API_KEY" \
.venv/bin/python -m app.cli.ingest_document \
  --file ./documento.txt \
  --title "Documento interno" \
  --source manual \
  --classification internal
```

Classificações suportadas:

```text
public
internal
confidential
```

A classificação solicitada não pode exceder o escopo autorizado para a credencial.

Por padrão, o CLI usa `access_mode=inherited`.

Quando o mesmo conteúdo já existe no mesmo escopo de deduplicação, a ingestão pode retornar:

```text
duplicate=true
chunks_inserted=0
```

## 7. RAG público

Exemplo mínimo:

```bash
curl -sS -X POST \
  http://127.0.0.1:8000/v1/rag/generate \
  -H "Content-Type: application/json" \
  -d '{"question":"What information is available?"}'
```

## 8. RAG autenticado

```bash
curl -sS -X POST \
  http://127.0.0.1:8000/v1/rag/generate-authenticated \
  -H "Authorization: Bearer $AEL_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"question":"Summarize the authorized internal knowledge."}'
```

O contrato também suporta parâmetros como `provider`, `external_approved`, `retrieval_limit`, `max_context_chunks`, `max_context_characters` e `temperature`.

## 9. Provider catalog

```bash
curl http://127.0.0.1:8000/v1/providers
```

A configuração padrão local usa `local_fast`.

Providers externos continuam sujeitos à política do sistema e às autorizações aplicáveis.

## 10. Testes

```bash
.venv/bin/python -m pytest -q
```

## 11. Encerramento

Para parar containers sem apagar dados:

```bash
docker compose --env-file .env -f infra/compose.yaml stop
```

Evite comandos destrutivos contra volumes que contenham dados necessários.
