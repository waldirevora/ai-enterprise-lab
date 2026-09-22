# Plano Experimental e Métricas

## 1. Objetivo

Transformar o AI Enterprise Lab de um sistema tecnicamente validado em um projeto acadêmico com evidências experimentais mensuráveis.

---

## 2. Regra principal

Resultados só podem ser registrados depois de coleta real.

A documentação distingue quatro estados:

```text
VALIDADO
PARCIALMENTE VALIDADO
PENDENTE DE MEDIÇÃO
NÃO APLICÁVEL AO DESENHO ATUAL
```

Uma validação funcional não deve ser apresentada automaticamente como benchmark de desempenho ou de escala.

---

## 3. Protocolo de caracterização A10

Para as medições controladas executadas em 22/09/2026 foi adotado:

```text
1 warm-up excluído das estatísticas
5 execuções medidas por componente
execução sequencial
mesmo hardware e serviços locais
sem concorrência artificial
```

Foram registrados, quando aplicável:

```text
mínimo
mediana
média
máximo
tokens
dimensão do embedding
similaridade
resultado funcional
citation/tool trace
```

Esses resultados caracterizam o laboratório atual. Não constituem benchmark universal dos modelos, do framework ou do hardware.

---

## 4. Experimento E01 — Startup local

**Objetivo:** medir o tempo necessário para o ambiente local atingir estado operacional.

### Protocolo executado

Foram executados 5 ciclos controlados, preservando os volumes persistentes.

Em cada ciclo foram observados PostgreSQL, Redis, API/readiness e n8n como serviço auxiliar.

### Resultados

API/readiness total:

| Métrica | Valor |
|---|---:|
| mínimo | 12.537,911 ms |
| mediana | 12.824,685 ms |
| média | 12.876,482 ms |
| máximo | 13.432,805 ms |

PostgreSQL/Redis healthy:

| Métrica | Valor |
|---|---:|
| mínimo | 11.938,936 ms |
| mediana | 12.198,596 ms |
| média | 12.150,032 ms |
| máximo | 12.230,486 ms |

O n8n apresentou tempo de healthcheck superior e foi tratado como serviço auxiliar, sem compor o critério principal de readiness da API.

**Resultado:** VALIDADO

---

## 5. Experimento E02 — Geração local_fast

Modelo:

```text
qwen2.5-coder:3b
```

### Caracterização A10 já coletada

Foi executado 1 warm-up e 5 solicitações medidas com prompt fixo, temperatura 0 e limite de saída controlado.

Resultado funcional:

```text
5/5 respostas contendo o marcador esperado
prompt_tokens=39 por execução
generated_tokens=7 por execução
```

Wall clock:

| Métrica | Valor |
|---|---:|
| mínimo | 309,222 ms |
| mediana | 323,017 ms |
| média | 340,931 ms |
| máximo | 382,778 ms |

Duração reportada pelo provider:

| Métrica | Valor |
|---|---:|
| mínimo | 262,040 ms |
| mediana | 289,290 ms |
| média | 284,994 ms |
| máximo | 309,530 ms |

### Métricas ainda não coletadas

```text
time-to-first-token
CPU
RAM
VRAM
execução formal com amostra maior
```

**Estado:** PARCIALMENTE VALIDADO

---

## 6. Experimento E03 — Geração local_deep

Modelo:

`qwen2.5-coder:7b-instruct-q3_K_S`

### Protocolo executado

Foi executado 1 warm-up excluído das estatísticas, seguido de 5 execuções sequenciais medidas.
A temperatura foi fixada em 0 e a saída limitada a 64 tokens.

### Resultados

As 5 execuções retornaram HTTP 200, provider/model corretos e 64 tokens gerados.

Wall clock mediano:

`7.335,776 ms`

Duração mediana reportada pelo provider:

`7.298,600 ms`

Como todas as execuções atingiram o limite de 64 tokens, a latência caracteriza uma saída limitada por esse teto.

A caracterização de CPU, RAM, VRAM e temperatura foi complementada posteriormente no E14.

**Resultado:** VALIDADO

---

## 7. Experimento E04 — Embeddings

Modelo:

```text
qwen3-embedding:0.6b
```

### Caracterização A10 já coletada

Dimensão:

```text
1024
```

A dimensão foi consistente em todas as execuções.

Wall clock para 5 execuções:

| Métrica | Valor |
|---|---:|
| mínimo | 42,010 ms |
| mediana | 52,836 ms |
| média | 51,910 ms |
| máximo | 61,266 ms |

### Métricas ainda não coletadas

```text
throughput com múltiplos chunks
memória
CPU
VRAM
```

**Estado:** PARCIALMENTE VALIDADO

---

## 8. Experimento E05 — Ingestão RAG

### Protocolo executado

Foi executado 1 warm-up excluído, seguido de 5 documentos medidos.
Cada documento continha 1000 palavras e produziu 6 chunks.
O pipeline incluiu chunking, embeddings locais, persistência em PostgreSQL/pgvector e cleanup posterior.

Parâmetros principais:

`chunk_size_words=220`

`overlap_words=40`

### Resultados

Tempo de ingestão medido:

| Métrica | Valor |
|---|---:|
| mediana | 3.059,056 ms |
| média | 2.844,063 ms |

As 5 execuções produziram os 6 chunks esperados por documento.
O cleanup restaurou o baseline após o experimento.

ACL não foi misturada neste experimento; sua avaliação permanece no E07.

**Resultado:** VALIDADO

---

## 9. Experimento E06 — Qualidade de retrieval

### Protocolo executado

Foi criado um corpus sintético controlado com 10 documentos semanticamente distintos e 10 queries com ground truth definido previamente.
Um documento persistente adicional permaneceu como distractor.
Cada documento temporário possuía 1 chunk e o retrieval utilizou `limit=20`.

O planejamento inicial previa pelo menos 20 perguntas; esta primeira execução formal utilizou 10 queries, e essa redução permanece registrada como limitação metodológica.

### Métricas

`Hit@1`

`Hit@3`

`Hit@5`

`MRR`

### Resultados

`queries=10`

`found_targets=10`

`Hit@1=1,000`

`Hit@3=1,000`

`Hit@5=1,000`

`MRR=1,000`

`mean_rank_found=1,000`

Latência de retrieval:

| Métrica | Valor |
|---|---:|
| mínimo | 98,806 ms |
| mediana | 121,008 ms |
| média | 119,302 ms |
| máximo | 141,292 ms |

Os 10 targets apareceram na primeira posição.
O resultado caracteriza esse corpus sintético pequeno e semanticamente separado; não permite inferir desempenho em corpus empresarial grande, ambíguo ou semanticamente denso.

**Estado:** VALIDADO NO CORPUS CONTROLADO

---

## 10. Experimento E07 — ACL do RAG

Cenários funcionais já validados:

```text
usuário autorizado → documento restrito recuperável
usuário da mesma organização sem ACL → documento restrito não recuperável
documento inherited → recuperável conforme escopo
documento secret fora da autorização → não recuperável
```

A validação HTTP autenticada demonstrou comportamento fail-closed e ausência de vazamento no cenário testado.

Ainda falta transformar esse conjunto em uma matriz experimental numericamente resumida.

**Estado:** VALIDADO FUNCIONALMENTE / MÉTRICA ACADÊMICA PENDENTE

---

## 11. Experimento E08 — Redis failure

### Protocolo executado

Foram executados 5 ciclos controlados de falha e recuperação do Redis.
Em cada ciclo, o Redis foi interrompido, a degradação da readiness foi confirmada e o serviço foi iniciado novamente sem reiniciar a API FastAPI.

Durante a indisponibilidade:

`/health=200`

`/ready=503`

Após a recuperação:

`/ready=200`

### Resultados

Tempo do comando de start do Redis:

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

A recuperação funcional da API ocorreu antes de o Docker declarar o container Redis como healthy.
Por isso, o tempo do healthcheck do Docker não deve ser interpretado como tempo real de recuperação da conectividade da aplicação.

**Estado:** VALIDADO

---

## 12. Experimento E09 — Persistência

Foi executada recreation real dos containers de PostgreSQL, n8n e Redis.

PostgreSQL:
- container foi recriado;
- volume foi preservado;
- contagens permaneceram iguais;
- documento 55 manteve o mesmo fingerprint.

n8n:
- container foi recriado;
- workflow `LAB - Persistence Test` permaneceu disponível.

Redis:
- foi tratado como estado transitório;
- não existe volume persistente;
- após recreation retornou `PONG`.

**Resultado:** VALIDADO

---

## 13. Experimento E10 — Migration idempotency

Foram validados:
- baseline;
- checksums;
- aplicação única;
- detecção de migration alterada;
- concorrência via advisory lock;
- status sem migrations futuras pendentes.

Estado observado após A9:

```text
baseline_schema: valid
baseline_registration: valid
future_migrations_applied: 0
future_migrations_pending: 0
```

**Resultado:** VALIDADO

---

## 14. Experimento E11 — Backup e restore

Backup real:

```text
app.dump=51.295 bytes
n8n.dump=467.339 bytes
checksums=OK
archives legíveis por pg_restore
diretório=0700
arquivos=0600
```

Restore:
- PostgreSQL temporário;
- volume temporário dedicado;
- nenhuma porta publicada;
- mesmo image family do PostgreSQL de origem;
- `app.dump` restaurado;
- `n8n.dump` restaurado;
- documento 55 preservado;
- seis migrations preservadas;
- workflow do n8n preservado;
- bancos originais intactos;
- cleanup completo dos recursos temporários.

Resultado:

```text
A9_ISOLATED_RESTORE_E2E=PASS
health=200
ready=200
```

**Resultado:** VALIDADO

---

## 15. Experimento E12 — Agente e tools

A arquitetura atual expõe ao agente somente a tool server-side:

```text
search_enterprise_knowledge
```

Não existe seleção dinâmica de tools pelo cliente no endpoint atual. Por isso, o cenário "tool proibida enviada pelo cliente" não se aplica ao desenho corrente.

### Validações funcionais

No A7:
- requisição sem credencial retornou 401;
- requisição autenticada retornou 200;
- retrieval ocorreu por tool server-side;
- citação do documento esperado foi retornada;
- tool trace foi registrado;
- provider policy foi exercitada por testes;
- timeout operacional antigo de 5 s foi identificado como insuficiente e corrigido para configuração explícita.

No A10, após warm-up, 5 execuções HTTP E2E tiveram:

```text
HTTP=200 em 5/5
steps_executed=2 em 5/5
citation_ok=true em 5/5
tool_ok=true em 5/5
prompt_tokens=288 por execução
generated_tokens=35 por execução
```

Wall clock:

| Métrica | Valor |
|---|---:|
| mínimo | 3.129,473 ms |
| mediana | 5.015,606 ms |
| média | 4.321,032 ms |
| máximo | 5.211,401 ms |

Warm-up, excluído das estatísticas:

```text
9.236,732 ms
```

A variação observada deve ser relatada sem atribuir causa específica sem instrumentação adicional.

**Estado:** VALIDADO FUNCIONALMENTE / CARACTERIZAÇÃO DE LATÊNCIA PARCIAL

---

## 16. Experimento E13 — Logs e secrets

### Protocolo executado

Foram utilizados somente canários sintéticos para verificar exposição em audit metadata, Authorization, headers, query strings, respostas HTTP e access logs reais do Uvicorn.

### Finding inicial

O sanitizador de auditoria descartou corretamente os campos sensíveis testados.

No teste real do runtime, o canário inserido em query string foi detectado no access log padrão do Uvicorn.

`query_canary_in_log=DETECTED`

Não houve evidência de exposição dos canários em Authorization, header customizado ou respostas HTTP.

### Correção

O access log padrão do Uvicorn foi desabilitado nos entrypoints controlados pelo projeto com `--no-access-log`.
`query_string` também foi adicionada à denylist de labels sensíveis das métricas.

### Regressão

`query_canary_in_log=NOT_FOUND`

`header_canary_in_log=NOT_FOUND`

`authorization_canary_in_log=NOT_FOUND`

Os mesmos canários também não apareceram nas respostas HTTP.

Validação do patch:

`17 testes direcionados passed`

`427 passed, 2 warnings`

PR #23 CI: PASS.
CI pós-merge em `main`: PASS.

Merge commit: `60658edd330bcf7e15f5cd4a76ce17f430b8c25a`.

**Resultado:** VALIDADO / FINDING CORRIGIDO

---

## 17. Experimento E14 — Recursos do notebook

### Ambiente

Ubuntu 24.04.5 LTS em WSL2.
CPU: Intel Core i5-8300H, 4 cores físicos e 8 threads.
RAM visível ao WSL: aproximadamente 15 GiB.
GPU: NVIDIA GeForce GTX 1050 Ti com 4 GiB de VRAM.

### Protocolo executado

Foram caracterizadas três fases: `cold_idle`, `loaded_idle` e `inference_load`.
A amostragem ocorreu em intervalo aproximado de 0,5 segundo usando `/proc` e `nvidia-smi`.

### Cold idle

| Métrica | Mediana |
|---|---:|
| CPU | 2,725% |
| RAM usada | 2.306,992 MiB |
| GPU util. | 0% |
| VRAM | 802 MiB |
| GPU temp. | 52 °C |

### Loaded idle

| Métrica | Mediana |
|---|---:|
| CPU | 1,879% |
| RAM usada | 2.689,908 MiB |
| GPU util. | 0% |
| VRAM | 3.107 MiB |
| GPU temp. | 56 °C |

### Inference load

| Métrica | Mediana | Máximo |
|---|---:|---:|
| CPU | 51,073% | 64,752% |
| RAM usada | 2.688,281 MiB | 2.702,582 MiB |
| GPU util. | 34% | 93% |
| VRAM | 3.114 MiB | 3.117 MiB |
| GPU temp. | 58 °C | 65 °C |

Residência do modelo entre cold idle e loaded idle:

`median_vram_delta=2305 MiB`

`median_ram_delta=382,916 MiB`

A temperatura de CPU e a potência não ficaram disponíveis no WSL2.
O experimento caracteriza recursos deste ambiente local; não constitui benchmark universal nem permite inferir capacidade de produção em escala.

**Resultado:** VALIDADO

---

## 18. Métricas complementares A10

### Suíte automatizada

```text
427 passed
2 warnings
pytest reported duration=1,96 s
wall clock medido=3,857 s
```

### Bancos

```text
ai_enterprise_lab=9.729.715 bytes
n8n=14.636.723 bytes
```

### Health, 10 requests

```text
min=1,092 ms
mediana=1,357 ms
média=3,964 ms
máximo=26,649 ms
```

### Readiness, 10 requests

```text
min=12,481 ms
mediana=13,574 ms
média=13,676 ms
máximo=15,901 ms
```

`/ready` executa checagens de dependências, portanto não deve ser comparado como endpoint equivalente a `/health`.

---

## 19. Tabela de resultados

| ID | Experimento | Métrica principal | Estado |
|---|---|---|---|
| E01 | Startup | tempo até ready | VALIDADO |
| E02 | local_fast | latência/tokens/recursos | PARCIALMENTE VALIDADO |
| E03 | local_deep | latência/tokens/recursos | VALIDADO |
| E04 | embeddings | latência/dimensão/recursos | PARCIALMENTE VALIDADO |
| E05 | ingestão | tempo/chunks | VALIDADO |
| E06 | retrieval | Hit@k/MRR | VALIDADO NO CORPUS CONTROLADO |
| E07 | ACL | bloqueios corretos | VALIDADO FUNCIONALMENTE |
| E08 | Redis failure | degradação/recuperação | VALIDADO |
| E09 | persistência | integridade | VALIDADO |
| E10 | migrations | idempotência/checksum | VALIDADO |
| E11 | backup/restore | integridade restaurada | VALIDADO |
| E12 | agents/tools | policy enforcement/E2E | VALIDADO FUNCIONALMENTE |
| E13 | logs/secrets | exposição | VALIDADO / FINDING CORRIGIDO |
| E14 | recursos | CPU/RAM/VRAM | VALIDADO |

---

## 20. Critério de conclusão acadêmica

A primeira versão acadêmica não precisa transformar todo item em benchmark completo, mas deve:

```text
executar ou justificar E01–E14
registrar resultados observados
distinguir validação funcional de medição quantitativa
declarar limitações
relacionar resultados aos objetivos
evitar generalização além do ambiente testado
```
