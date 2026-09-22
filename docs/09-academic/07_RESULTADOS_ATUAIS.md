# Resultados Atuais

## 1. Regra de interpretação

Este documento registra somente resultados efetivamente observados.

As categorias usadas são:
- implementação existente;
- teste automatizado;
- validação funcional real;
- medição quantitativa;
- limitação.

Nenhuma medição local deve ser apresentada como benchmark universal.

---

## 2. Testes automatizados

Baseline atual:

```text
424 passed
2 warnings
```

Tempo reportado pelo pytest:

```text
1,96 s
```

Wall clock medido externamente:

```text
3,857 s
```

Warnings conhecidos:
- depreciação Starlette TestClient/httpx;
- depreciação AnyIO BlockingPortal.

Os warnings não bloquearam a suíte.

---

## 3. CI

O fluxo de CI permanece validado em Python 3.12.

O PR #21, referente à configuração de timeouts do runtime de agentes, foi aprovado no CI antes do merge e o `main` também passou no CI após o merge.

Commit de referência usado nas coletas A8–A10:

```text
cb0d3403e261be990c53be5fc0467862f2d5b391
```

---

## 4. Imagem de runtime

Validação já realizada:

```text
image_user=10001:10001
runtime_uid=10001
runtime_gid=10001
```

O CLI de migrations também foi executado dentro da imagem.

---

## 5. Redis

O Redis de produção-equivalent foi corrigido para execução non-root.

Resultado validado:

```text
redis_uid=999
REDIS NON-ROOT: OK
```

No Compose local, Redis não possui volume persistente e está configurado como estado transitório.

---

## 6. Readiness

Com dependências disponíveis:

```text
/health=200
/ready=200
```

Com Redis indisponível:

```text
/health=200
/ready=503
```

Após recuperação:

```text
/ready=200
```

No A8, depois de recreation dos containers, houve uma resposta transitória `503` e depois 10/10 respostas `200` sem reinício do FastAPI.

Isso demonstra comportamento fail-closed durante indisponibilidade e recuperação automática quando as dependências voltam.

---

## 7. Proxy/TLS local equivalente a produção

No ambiente de validação:

```text
HTTPS /health=200
HTTPS /ready=200
HTTP redirect=308
```

TLS público ACME continua pendente de VPS real.

---

## 8. Portas de produção

Contrato validado:

```text
FastAPI: sem porta publicada no host
PostgreSQL: sem porta publicada no host
Redis: sem porta publicada no host
n8n: 127.0.0.1:5678
Caddy: 80/443
```

---

## 9. Migrations

Foram validados:
- baseline histórico;
- checksum;
- apply-once;
- detecção de migration alterada;
- lock concorrente;
- status após aplicação.

Estado após o A9:

```text
baseline_schema: valid
baseline_registration: valid
future_migrations_applied: 0
future_migrations_pending: 0
```

Seis migrations foram preservadas no restore isolado.

---

## 10. Agente local funcional

No A7, o endpoint:

```text
POST /v1/agents/enterprise-knowledge/run
```

foi exercitado com infraestrutura real.

Resultados:
- sem credencial: 401;
- com credencial temporária válida: 200;
- provider `local_fast`;
- backend Ollama;
- dois passos executados;
- documento esperado citado;
- tool trace concluído;
- fixture temporária removida.

O teste inicial identificou que um timeout fixo de 5 s era insuficiente para retrieval real. O timeout da tool foi tornado configurável, com default de 20 s, e a suíte completa passou após a correção.

---

## 11. Persistência e recreation

No A8 foram recriados, individualmente:
- PostgreSQL;
- n8n;
- Redis.

PostgreSQL:
- novo container;
- mesmo volume;
- `organizations=1`;
- `rag_documents=1`;
- `rag_document_chunks=1`;
- `schema_migrations=6`;
- documento 55 preservado com o mesmo hash.

n8n:
- novo container;
- workflow preservado:

```text
id=cTrOa3T41DRABrfn
name=LAB - Persistence Test
active=false
```

Redis:
- novo container;
- `PING=PONG`;
- estado tratado como transitório.

**Resultado:** persistência/restart local aprovado.

---

## 12. Backup e restore

Backup real produzido:

```text
app.dump=51.295 bytes
n8n.dump=467.339 bytes
```

Validações:
- checksum dos dois arquivos: OK;
- leitura por `pg_restore -l`: OK;
- diretório: 0700;
- arquivos: 0600;
- manifest associado ao commit atual.

Restore real:
- PostgreSQL temporário;
- volume temporário dedicado;
- nenhuma porta publicada;
- `app.dump` restaurado;
- `n8n.dump` restaurado;
- documento 55 preservado;
- seis migrations preservadas;
- workflow n8n preservado;
- bancos originais intactos;
- container/volume temporários removidos.

Resultado:

```text
A9_ISOLATED_RESTORE_E2E=PASS
```

Depois do cleanup:

```text
health=200
ready=200
```

---

## 13. Caracterização de health/readiness

Foram feitas 10 solicitações locais para cada endpoint.

### `/health`

```text
mínimo=1,092 ms
mediana=1,357 ms
média=3,964 ms
máximo=26,649 ms
```

### `/ready`

```text
mínimo=12,481 ms
mediana=13,574 ms
média=13,676 ms
máximo=15,901 ms
```

A readiness inclui dependências e, por isso, tem responsabilidade diferente do health endpoint.

---

## 14. Embeddings

Modelo:

```text
qwen3-embedding:0.6b
```

Protocolo:
- 1 warm-up excluído;
- 5 execuções sequenciais medidas.

Dimensão:

```text
1024
```

Wall clock:

```text
mínimo=42,010 ms
mediana=52,836 ms
média=51,910 ms
máximo=61,266 ms
```

A dimensão permaneceu consistente em todas as execuções.

---

## 15. RAG retrieval

Dataset atual:

```text
organizations=1
rag_documents=1
rag_document_chunks=1
classification=public
access_mode=inherited
```

Em 5/5 execuções:

```text
top_document_id=55
top_similarity=0,759571
```

Wall clock:

```text
mínimo=87,080 ms
mediana=97,128 ms
média=96,645 ms
máximo=107,383 ms
```

Esse resultado comprova o comportamento do fluxo no dataset atual, mas não permite inferir qualidade em corpus maior.

---

## 16. Geração local_fast

Modelo:

```text
qwen2.5-coder:3b
```

Protocolo:
- 1 warm-up excluído;
- 5 execuções sequenciais;
- prompt fixo;
- temperatura 0;
- saída esperada conhecida.

Resultado:

```text
5/5 respostas válidas
prompt_tokens=39 por execução
generated_tokens=7 por execução
```

Wall clock:

```text
mínimo=309,222 ms
mediana=323,017 ms
média=340,931 ms
máximo=382,778 ms
```

Duração reportada pelo provider:

```text
mínimo=262,040 ms
mediana=289,290 ms
média=284,994 ms
máximo=309,530 ms
```

---

## 17. Agente HTTP E2E

Warm-up:

```text
9.236,732 ms
```

O warm-up não entrou nas estatísticas.

Cinco execuções medidas:

```text
5/5 HTTP=200
5/5 steps_executed=2
5/5 citation_ok=true
5/5 tool_ok=true
prompt_tokens=288 por execução
generated_tokens=35 por execução
```

Wall clock:

```text
mínimo=3.129,473 ms
mediana=5.015,606 ms
média=4.321,032 ms
máximo=5.211,401 ms
```

A variação entre as execuções é um resultado observado. Não foi atribuída causalidade específica porque não houve instrumentação suficiente para separar tempo de embedding, retrieval, geração e efeitos de estado quente/frio em todas as camadas.

---

## 18. Privacidade das métricas

A implementação de observabilidade possui métricas para:
- HTTP;
- geração;
- RAG;
- agentes;
- tokens;
- custo externo estimado;
- rate limiting.

O contrato proíbe labels sensíveis, incluindo:
- prompt;
- contexto;
- credencial;
- API key;
- document ID;
- principal ID;
- organization ID;
- response.

Há testes específicos para essa propriedade.

---

## 19. Resultados ainda pendentes

Ainda faltam medições formais de:

```text
startup completo
local_deep em série controlada
CPU
RAM
VRAM
temperatura
ingestão em corpus controlado
Hit@1/Hit@3/Hit@5/MRR em conjunto de perguntas
tempo exato de Redis recovery
inspeção acadêmica com canários em logs/secrets
```

---

## 20. Situação acadêmica atual

O laboratório já possui evidências reais de:
- correção automatizada;
- CI;
- isolamento e segurança de runtime;
- readiness fail-closed;
- RAG funcional;
- ACL funcional;
- agentes com tool server-side;
- persistência;
- backup e restore;
- observabilidade;
- geração local;
- métricas quantitativas iniciais.

As conclusões devem continuar limitadas ao ambiente testado, especialmente porque:
- o dataset RAG é mínimo;
- as séries quantitativas principais têm `n=5`;
- ainda não houve carga concorrente;
- ainda não houve deployment público real em VPS.
