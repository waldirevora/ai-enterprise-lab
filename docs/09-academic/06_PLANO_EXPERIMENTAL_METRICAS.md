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

### Procedimento

1. Encerrar stack.
2. Registrar timestamp.
3. Subir dependências.
4. Iniciar API.
5. Aguardar readiness 200.
6. Registrar tempo total.

### Métricas

```text
tempo até PostgreSQL healthy
tempo até Redis healthy
tempo até API ready
tempo total
```

**Resultado:** PENDENTE DE MEDIÇÃO

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

```text
qwen2.5-coder:7b-instruct-q3_K_S
```

Objetivo: caracterizar latência e recursos no mesmo protocolo utilizado para `local_fast`.

Há smoke test funcional anterior, mas não existe ainda uma série controlada equivalente ao A10.

**Resultado:** PENDENTE DE MEDIÇÃO

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

### Dataset planejado

Criar corpus controlado com:
- documento A;
- documento B;
- documento C;
- pelo menos um documento com ACL restrita.

### Métricas

```text
tempo de ingestão
chunks gerados
tempo de embeddings
registros persistidos
```

O fluxo de ingestão já foi validado funcionalmente, mas o experimento com corpus controlado ainda não foi executado.

**Resultado:** PENDENTE DE MEDIÇÃO

---

## 9. Experimento E06 — Qualidade de retrieval

O experimento formal deve usar no mínimo 20 perguntas com fonte correta conhecida.

### Métricas

```text
Hit@1
Hit@3
Hit@5
MRR
```

### Caracterização A10

No dataset mínimo atual, com 1 documento e 1 chunk:

```text
5/5 execuções retornaram document_id=55 como primeiro resultado
similaridade=0,759571 em todas as execuções
```

Wall clock:

| Métrica | Valor |
|---|---:|
| mínimo | 87,080 ms |
| mediana | 97,128 ms |
| média | 96,645 ms |
| máximo | 107,383 ms |

Esse resultado confirma repetibilidade no estado atual, mas não permite inferir qualidade de retrieval em corpus real.

**Estado:** PARCIALMENTE VALIDADO

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

Comportamento observado:

```text
Redis indisponível:
health=200
ready=503

Redis recuperado:
ready=200
```

No A8, após recreation dos serviços, houve uma janela transitória de `ready=503`; sem reiniciar a API, a readiness se recuperou e retornou `200` em 10/10 tentativas subsequentes.

Ainda falta medir de forma controlada o tempo exato de recovery.

**Estado:** PARCIALMENTE VALIDADO

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

Existem testes de sanitização, privacidade de métricas e ausência de labels sensíveis.

Ainda falta uma inspeção acadêmica controlada e documentada dos logs do runtime com valores-canário específicos.

**Resultado:** PENDENTE LOCAL REAL

---

## 17. Experimento E14 — Recursos do notebook

Medir durante workloads de geração:
- RAM;
- CPU;
- VRAM;
- armazenamento;
- temperatura, se disponível.

**Resultado:** PENDENTE

---

## 18. Métricas complementares A10

### Suíte automatizada

```text
424 passed
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
| E01 | Startup | tempo até ready | PENDENTE |
| E02 | local_fast | latência/tokens/recursos | PARCIALMENTE VALIDADO |
| E03 | local_deep | latência/tokens/recursos | PENDENTE |
| E04 | embeddings | latência/dimensão/recursos | PARCIALMENTE VALIDADO |
| E05 | ingestão | tempo/chunks | PENDENTE |
| E06 | retrieval | Hit@k/MRR | PARCIALMENTE VALIDADO |
| E07 | ACL | bloqueios corretos | VALIDADO FUNCIONALMENTE |
| E08 | Redis failure | degradação/recuperação | PARCIALMENTE VALIDADO |
| E09 | persistência | integridade | VALIDADO |
| E10 | migrations | idempotência/checksum | VALIDADO |
| E11 | backup/restore | integridade restaurada | VALIDADO |
| E12 | agents/tools | policy enforcement/E2E | VALIDADO FUNCIONALMENTE |
| E13 | logs/secrets | exposição | PENDENTE LOCAL REAL |
| E14 | recursos | CPU/RAM/VRAM | PENDENTE |

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
