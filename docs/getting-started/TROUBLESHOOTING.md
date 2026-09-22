# Troubleshooting
\n**Idioma:** Português (Brasil) | [English](TROUBLESHOOTING_EN.md)

Este guia cobre falhas comuns do ambiente local do AI Enterprise Lab.

## 1. `/ready` não retorna ready

Confirme os serviços:

```bash
docker compose --env-file .env -f infra/compose.yaml ps
```

Confira PostgreSQL e Redis antes de investigar a camada de IA.

```bash
.venv/bin/python -m app.db.migrations status
```

A readiness pode falhar quando uma dependência obrigatória não está disponível.

## 2. PostgreSQL password is not configured

Confirme que `.env` contém um valor para:

```text
POSTGRES_PASSWORD=
```

Não publique o valor em logs ou issues.

## 3. Docker Compose não inicia

Valide a configuração sem materializar secrets na saída:

```bash
docker compose --env-file .env -f infra/compose.yaml config --quiet
```

Depois consulte:

```bash
docker compose --env-file .env -f infra/compose.yaml ps
```

## 4. Ollama ou modelo indisponível

Confirme que o Ollama está executando:

```bash
ollama list
```

Os modelos padrão são:

```text
qwen2.5-coder:3b
qwen2.5-coder:7b-instruct-q3_K_S
qwen3-embedding:0.6b
```

Se necessário:

```bash
ollama pull qwen2.5-coder:3b
ollama pull qwen2.5-coder:7b-instruct-q3_K_S
ollama pull qwen3-embedding:0.6b
```

## 5. API retorna 401

Endpoints autenticados exigem:

```text
Authorization: Bearer <API_KEY>
```

Chave ausente, formato inválido, credencial revogada ou contexto de acesso inválido podem resultar em falha de autenticação.

Nunca coloque a API key na URL.

## 6. `AEL_API_KEY is not configured`

Carregue a credencial na sessão:

```bash
export AEL_API_KEY="<API_KEY>"
```

## 7. Classificação acima do escopo

O CLI de ingestão recusa documentos cuja classificação solicitada exceda o escopo da credencial.

Use uma classificação permitida ou ajuste o membership por um fluxo administrativo apropriado.

Não altere o cliente para tentar contornar a autorização do servidor.

## 8. Documento aparece como duplicado

Uma resposta como:

```text
duplicate=true
chunks_inserted=0
```

indica que o conteúdo já foi encontrado no escopo de deduplicação usado pela ingestão.

## 9. Migration inconsistente

Inspecione:

```bash
.venv/bin/python -m app.db.migrations verify
.venv/bin/python -m app.db.migrations status
```

Para aplicar migrations pendentes:

```bash
.venv/bin/python -m app.db.migrations apply
```

Não execute manualmente os scripts históricos `001` a `006` por cima de um banco já inicializado.

## 10. Porta já está em uso

As portas locais mais relevantes incluem `8000`, `5432`, `6379`, `5678` e `11434`.

Identifique o processo ou container que já ocupa a porta antes de mudar a configuração.

## 11. Testes falhando

Execute primeiro a suíte completa:

```bash
.venv/bin/python -m pytest -q
```

Depois isole o arquivo ou teste afetado com pytest.

## 12. Antes de abrir uma issue

Registre a etapa que falhou, comando executado, código de retorno, mensagem de erro sanitizada e ambiente utilizado.

Remova API keys, senhas, tokens, `.env`, dados empresariais e qualquer outro secret antes de compartilhar logs.

## 13. Credencial revogada

Uma API key revogada deixa de autenticar imediatamente.

Para revogar a chave carregada em `AEL_API_KEY`:

```bash
AEL_API_KEY="$AEL_API_KEY" \
.venv/bin/python -m app.cli.revoke_api_key
```

Se uma nova credencial for necessária, gere outra por um fluxo administrativo autorizado. Não tente reativar diretamente uma credencial revogada.
