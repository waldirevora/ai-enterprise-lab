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

Baseline atual após a correção do E13:

```text
427 passed
2 warnings
```

Warnings conhecidos:
- depreciação Starlette TestClient/httpx;
- depreciação AnyIO BlockingPortal.

Os warnings não bloquearam a suíte.

A contagem aumentou de 424 para 427 devido aos novos testes de regressão relacionados ao runtime e à privacidade dos access logs.

---

## 3. CI

O fluxo de CI permanece validado em Python 3.12.

No E13, o PR #23 passou no CI antes do merge.

```text
PR #23
head=028f8e8e97caad40442dbe9b4b7adc9d1ee531af
PR CI=success
```

O squash merge gerou:

```text
60658edd330bcf7e15f5cd4a76ce17f430b8c25a
```

O CI pós-merge em `main` também concluiu com sucesso:

```text
run_id=35753817461
event=push
conclusion=success
```

O workflow executou instalação e verificação de dependências, compilação das fontes Python, suíte de testes e auditoria das dependências runtime.

O commit `cb0d3403e261be990c53be5fc0467862f2d5b391` permanece como referência histórica das coletas A8–A10.

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

### Comportamento funcional

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

No A8, após recreation dos containers, houve uma resposta transitória `503` e depois 10/10 respostas `200` sem reinício do FastAPI.

### E08 — recuperação controlada do Redis

Foram executados 5 ciclos controlados de falha e recuperação sem reiniciar a API.

Tempo do comando de start:

| Métrica | Valor |
|---|---:|
| mínimo | 402,295 ms |
| mediana | 427,907 ms |
| média | 432,136 ms |
| máximo | 485,410 ms |

Tempo até o Docker marcar Redis como healthy:

| Métrica | Valor |
|---|---:|
| mínimo | 10.300,122 ms |
| mediana | 10.387,633 ms |
| média | 10.404,513 ms |
| máximo | 10.569,350 ms |

Tempo até a API recuperar `/ready=200`:

| Métrica | Valor |
|---|---:|
| mínimo | 572,620 ms |
| mediana | 643,790 ms |
| média | 645,586 ms |
| máximo | 749,384 ms |

A recuperação funcional da aplicação ocorreu antes do estado `healthy` do Docker.
O intervalo do healthcheck do container é mais conservador e não representa o instante exato em que a aplicação voltou a aceitar Redis.

**Resultado E08:** VALIDADO

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

## 15. RAG — ingestão e retrieval

### E05 — Ingestão RAG

O E05 mediu separadamente a etapa de ingestão, sem misturar ACL ou avaliação de retrieval.

Protocolo:

```text
1 warm-up excluído
5 documentos medidos
1000 palavras por documento
6 chunks por documento
chunk_size_words=220
overlap_words=40
```

O pipeline incluiu chunking, embeddings locais, persistência em PostgreSQL/pgvector e cleanup posterior.

Tempo de ingestão:

| Métrica | Valor |
|---|---:|
| mediana | 3.059,056 ms |
| média | 2.844,063 ms |

As 5 execuções produziram os 6 chunks esperados por documento.
O cleanup restaurou o baseline após o experimento.

**Resultado E05:** VALIDADO

### Baseline histórico A10

O A10 utilizou o estado mínimo então disponível:

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

Wall clock A10:

| Métrica | Valor |
|---|---:|
| mínimo | 87,080 ms |
| mediana | 97,128 ms |
| média | 96,645 ms |
| máximo | 107,383 ms |

Esse baseline comprova repetibilidade do fluxo mínimo, mas não mede qualidade de retrieval em corpus múltiplo.

### E06 — corpus controlado

Foi executado um experimento formal com 10 documentos sintéticos semanticamente distintos e 10 queries com ground truth definido previamente.
Um documento persistente adicional permaneceu como distractor.
Cada documento temporário possuía 1 chunk e o retrieval utilizou `limit=20`.

Resultados:

```text
queries=10
found_targets=10
Hit@1=1,000
Hit@3=1,000
Hit@5=1,000
MRR=1,000
mean_rank_found=1,000
```

Latência E06:

| Métrica | Valor |
|---|---:|
| mínimo | 98,806 ms |
| mediana | 121,008 ms |
| média | 119,302 ms |
| máximo | 141,292 ms |

Os 10 targets foram recuperados na primeira posição.

O planejamento inicial previa pelo menos 20 perguntas, mas esta primeira execução formal utilizou 10 queries.
O resultado é válido para esse corpus pequeno, sintético e semanticamente separado, não para inferir desempenho em corpus empresarial grande, ambíguo ou semanticamente denso.

**Resultado E06:** VALIDADO NO CORPUS CONTROLADO

---

## 16. Geração local

### local_fast

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

### E03 — Geração local_deep

Modelo:

```text
qwen2.5-coder:7b-instruct-q3_K_S
```

Protocolo:
- 1 warm-up excluído;
- 5 execuções sequenciais medidas;
- temperatura 0;
- `max_output_tokens=64`;
- contexto de 4096 tokens.

Resultado:

```text
5/5 HTTP=200
64 generated_tokens por execução
```

Wall clock mediano:

```text
7.335,776 ms
```

Duração mediana reportada pelo provider:

```text
7.298,600 ms
```

Como todas as execuções atingiram o limite de 64 tokens, a latência caracteriza uma saída limitada por esse teto.
A caracterização de recursos do mesmo modelo é apresentada separadamente no E14.

**Resultado E03:** VALIDADO

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

## 18. Observabilidade, privacidade e recursos

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

### E13 — Logs e secrets

O experimento utilizou exclusivamente canários sintéticos para verificar possível exposição de dados sensíveis.

Foram verificados:
- audit metadata;
- Authorization;
- header customizado;
- query string;
- respostas HTTP;
- access log real do Uvicorn.

#### Finding inicial

O sanitizador de auditoria descartou corretamente os campos sensíveis testados.

No runtime real, porém, o canário inserido em query string apareceu no access log padrão do Uvicorn:

```text
query_canary_in_log=DETECTED
```

Os canários de Authorization, header customizado e respostas HTTP não foram encontrados.

#### Correção

O access log padrão do Uvicorn foi desabilitado nos entrypoints controlados pelo projeto com `--no-access-log`.
`query_string` também foi adicionada à denylist de labels sensíveis das métricas.

#### Regressão

```text
query_canary_in_log=NOT_FOUND
header_canary_in_log=NOT_FOUND
authorization_canary_in_log=NOT_FOUND
```

Os mesmos canários também não apareceram nas respostas HTTP.

Validação do patch:

```text
17 testes direcionados passed
427 passed
2 warnings
PR #23 CI=success
main post-merge CI=success
```

**Resultado E13:** VALIDADO / FINDING CORRIGIDO

### E14 — Recursos do sistema

A caracterização foi realizada em Ubuntu 24.04.5 LTS sobre WSL2.

Hardware observado:

```text
CPU: Intel Core i5-8300H, 4 cores / 8 threads
RAM visível ao WSL: aproximadamente 15 GiB
GPU: NVIDIA GeForce GTX 1050 Ti, 4 GiB VRAM
```

Foram avaliadas três fases: `cold_idle`, `loaded_idle` e `inference_load`.

#### Cold idle

| Métrica | Mediana |
|---|---:|
| CPU | 2,725% |
| RAM usada | 2.306,992 MiB |
| GPU util. | 0% |
| VRAM | 802 MiB |
| GPU temp. | 52 °C |

#### Loaded idle

| Métrica | Mediana |
|---|---:|
| CPU | 1,879% |
| RAM usada | 2.689,908 MiB |
| GPU util. | 0% |
| VRAM | 3.107 MiB |
| GPU temp. | 56 °C |

#### Inference load

Foram executadas 3 gerações sequenciais com o modelo `local_deep`, enquanto os recursos eram amostrados.

| Métrica | Mediana | Máximo |
|---|---:|---:|
| CPU | 51,073% | 64,752% |
| RAM usada | 2.688,281 MiB | 2.702,582 MiB |
| GPU util. | 34% | 93% |
| VRAM | 3.114 MiB | 3.117 MiB |
| GPU temp. | 58 °C | 65 °C |

Residência observada entre cold idle e loaded idle:

```text
median_vram_delta=2305 MiB
median_ram_delta=382,916 MiB
```

O RSS do processo FastAPI permaneceu aproximadamente estável em 78,785 MiB durante a caracterização.

A temperatura de CPU e a potência não ficaram disponíveis no ambiente WSL2.
O E14 possui apenas 3 gerações sob carga e utiliza amostragem com `nvidia-smi`; portanto, caracteriza recursos deste laboratório e não capacidade de produção em escala.
As latências observadas durante E14 não devem ser comparadas diretamente com E03 porque protocolo, estado do sistema e instrumentação são diferentes.

**Resultado E14:** VALIDADO

---

## 19. Medições e validações ainda abertas

Os experimentos E01, E03, E05, E06, E08, E13 e E14 deixaram de estar pendentes e possuem resultados registrados neste documento.

As lacunas que permanecem abertas são extensões da caracterização atual:

- E02 `local_fast`: time-to-first-token, recursos e amostra formal maior;
- E04 embeddings: throughput com múltiplos chunks e caracterização de recursos;
- E07 ACL: consolidação dos cenários já validados em matriz quantitativa acadêmica;
- E12 agents/tools: decomposição mais detalhada da latência por etapa;
- testes com carga concorrente;
- deployment público real em VPS;
- validação real de DNS, firewall e ACME;
- caracterização de escala e capacidade sob condições de produção.

Esses itens permanecem como trabalhos futuros e não devem ser confundidos com ausência de validação funcional das respectivas camadas já testadas.

---

## 20. Situação acadêmica atual

O laboratório possui evidências reais de:
- suíte automatizada com 427 testes aprovados;
- CI antes e depois do merge;
- isolamento e segurança de runtime;
- readiness fail-closed e recuperação automática do Redis;
- ingestão RAG controlada;
- retrieval com Hit@1, Hit@3, Hit@5 e MRR medidos;
- ACL funcional;
- agentes com tool server-side;
- persistência após recreation;
- backup e restore isolado;
- observabilidade com restrição de labels sensíveis;
- inspeção real de logs com finding identificado, corrigido e retestado;
- geração local_fast e local_deep;
- caracterização de CPU, RAM, GPU, VRAM e temperatura de GPU.

### Limites de interpretação

O baseline histórico A10 utilizava apenas 1 documento e 1 chunk.
O E06 ampliou a avaliação para 10 documentos sintéticos, 10 queries e 1 distractor persistente, mas o corpus continua pequeno, sintético e semanticamente separado.

As principais séries controladas utilizam amostras pequenas, normalmente `n=5`.
O E14 utilizou 3 gerações sequenciais durante a caracterização sob carga.

Não houve carga concorrente nem deployment público real em VPS.
O E14 foi executado em WSL2, e temperatura de CPU e potência não estavam disponíveis.

E02, E04, E07 e E12 permanecem parcialmente caracterizados em aspectos específicos, conforme o plano experimental.

Portanto, os resultados sustentam a validação da arquitetura e de seus principais mecanismos no ambiente local testado, mas não constituem benchmark universal nem demonstração de capacidade de produção em escala.
