# Roteiro de Apresentação Acadêmica

## Duração sugerida

10 a 15 minutos.

---

## Slide 1 — Problema

Mensagem:

> Aplicações empresariais de IA precisam de mais do que um modelo capaz de responder perguntas.

Apresentar:
- dados privados;
- autorização;
- RAG;
- ferramentas;
- observabilidade;
- deployment.

---

## Slide 2 — Questão de pesquisa

> Como estruturar uma arquitetura local e privada de IA generativa com RAG, agentes, segurança e observabilidade?

---

## Slide 3 — Objetivo

Mostrar objetivo geral e 4–5 objetivos específicos.

---

## Slide 4 — Arquitetura

```text
Caddy
→ FastAPI
→ PostgreSQL/pgvector
→ Redis
→ Ollama
→ n8n
```

Explicar que providers e tools são controlados por política.

---

## Slide 5 — RAG

Mostrar o fluxo:

```text
documento
→ chunking
→ embedding
→ pgvector
→ autorização
→ retrieval
→ contexto
→ geração
```

Resultados principais:
- E05: documentos de 1000 palavras produziram 6 chunks; mediana de ingestão = 3.059,056 ms;
- E06: 10 documentos sintéticos + 1 distractor e 10 queries com ground truth;
- Hit@1 = 1,000; Hit@3 = 1,000; Hit@5 = 1,000; MRR = 1,000;
- mediana de retrieval E06 = 121,008 ms.

Explicar que o corpus é pequeno, sintético e semanticamente separado. O resultado demonstra funcionamento no corpus controlado, não qualidade universal em escala empresarial.

---

## Slide 6 — Segurança

Mostrar:
- deny-by-default;
- ACL;
- execução non-root;
- secrets fora do código;
- trusted proxy;
- audit trail;
- rate limiting;
- métricas sem labels sensíveis.

Caso E13:
- canário em query string foi encontrado no access log padrão do Uvicorn;
- access log foi desabilitado com `--no-access-log` nos entrypoints controlados;
- `query_string` entrou na denylist das métricas;
- regressão confirmou ausência dos canários em logs e respostas.

Mensagem principal: o experimento encontrou um risco real, o projeto foi corrigido e o mesmo cenário foi retestado.

---

## Slide 7 — Engenharia e confiabilidade

Mostrar:
- 427 testes automatizados aprovados;
- CI no PR e novamente após merge em `main`;
- migrations com checksums e idempotência;
- persistência após recreation;
- backup e restore isolado;
- readiness fail-closed;
- rollback documentado.

Exemplo de resiliência E08:

```text
Redis indisponível: /health=200 e /ready=503
Redis recuperado: /ready=200 sem reiniciar a API
mediana de recuperação funcional = 643,790 ms
```

Distinguir recuperação funcional da API do healthcheck mais conservador do Docker.

---

## Slide 8 — Demonstração

Fluxo sugerido:

```text
1. mostrar health/readiness
2. consultar documento
3. mostrar retrieval/citação
4. executar agente
5. mostrar tool trace
6. mostrar audit
7. tentar acesso sem permissão
8. mostrar bloqueio
```

---

## Slide 9 — Experimentos

Explicar que o projeto passou de validação funcional para caracterização experimental controlada.

Protocolo recorrente:

```text
warm-up excluído quando aplicável
execuções sequenciais
mesmo ambiente local
sem concorrência artificial
mínimo / mediana / média / máximo quando disponíveis
```

Experimentos consolidados:
- E01: startup local;
- E03: geração `local_deep`;
- E05: ingestão RAG;
- E06: qualidade de retrieval;
- E08: falha e recuperação do Redis;
- E13: logs e secrets;
- E14: CPU, RAM, GPU, VRAM e temperatura de GPU.

Também permanecem as caracterizações anteriores de embeddings, `local_fast`, agente E2E, health/readiness, persistência e backup/restore.

Mensagem metodológica: são resultados do ambiente testado, não benchmark universal.

---

## Slide 10 — Resultados

Selecionar poucos resultados representativos:

```text
427 testes aprovados

local_fast:
mediana wall clock = 323,017 ms

local_deep:
mediana wall clock = 7.335,776 ms

E06 retrieval:
Hit@1 = 1,000
Hit@3 = 1,000
Hit@5 = 1,000
MRR = 1,000
mediana = 121,008 ms

E08 Redis recovery:
mediana até /ready=200 = 643,790 ms

E13:
finding de query string no access log = corrigido e retestado

E14:
GPU util. máxima = 93%
GPU temp. máxima = 65 °C

backup/restore:
restore isolado = PASS
```

Durante a apresentação, não interpretar diferenças de latência entre experimentos distintos como regressão sem protocolo diretamente comparável.

---

## Slide 11 — Limitações

Apresentar somente limitações que continuam reais:
- hardware local com GPU de 4 GB de VRAM;
- E06 com 10 documentos sintéticos, 10 queries e 1 distractor: corpus ainda pequeno e semanticamente separado;
- principais séries controladas com amostras pequenas, normalmente `n=5`;
- E14 com apenas 3 gerações sequenciais durante `inference_load`;
- ambiente de caracterização em WSL2;
- temperatura de CPU e potência não disponíveis;
- sem carga concorrente;
- sem alta disponibilidade;
- sem IAM corporativo completo;
- sem deployment público real em VPS, DNS e ACME;
- E02, E04, E07 e E12 ainda parcialmente caracterizados em aspectos específicos.

Mensagem principal: os experimentos sustentam o funcionamento da arquitetura no ambiente local testado, mas não demonstram capacidade de produção em escala.

---

## Slide 12 — Conclusão

Mensagem:

> O resultado do projeto não é apenas um chatbot, mas uma arquitetura de referência para operar IA de forma controlada, observável e reproduzível.

Fechar distinguindo:
- o que foi demonstrado no laboratório;
- o que ainda precisa ser validado em deployment real e em experimentos de maior escala.
