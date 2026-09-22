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

Demonstrar:

```text
documento
→ embedding
→ pgvector
→ autorização
→ retrieval
→ contexto
→ geração
```

Resultado local atual:
- documento esperado recuperado em 5/5 execuções da caracterização;
- similaridade observada 0,759571;
- dataset ainda mínimo, sem alegação de qualidade em escala.

---

## Slide 6 — Segurança

Mostrar:
- deny-by-default;
- ACL;
- non-root;
- secrets;
- trusted proxy;
- audit;
- rate limiting;
- métricas sem labels sensíveis.

---

## Slide 7 — Engenharia e confiabilidade

Mostrar:
- 424 testes;
- CI;
- migrations;
- checksums;
- persistence/restart;
- backup/restore isolado;
- readiness;
- rollback.

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

Mostrar o protocolo:

```text
1 warm-up excluído
5 execuções sequenciais
mínimo / mediana / média / máximo
```

Apresentar como caracterização local, não benchmark universal.

Exemplos medidos:
- embedding;
- retrieval;
- geração `local_fast`;
- agente E2E;
- health/readiness.

---

## Slide 10 — Resultados

Exemplos:

```text
424 testes aprovados

local_fast:
mediana wall clock = 323,017 ms

embedding:
mediana = 52,836 ms
dimensão = 1024

retrieval:
mediana = 97,128 ms
documento esperado = 5/5

agente E2E:
mediana = 5.015,606 ms
HTTP 200 + citação + tool trace = 5/5

backup/restore:
restore isolado = PASS
```

Separar claramente:
- resultado validado;
- caracterização parcial;
- medição ainda pendente.

---

## Slide 11 — Limitações

- hardware com 4 GB de VRAM;
- dataset RAG de 1 documento/1 chunk nas métricas atuais;
- séries principais com `n=5`;
- sem carga concorrente;
- sem CPU/RAM/VRAM acadêmicos sincronizados;
- sem HA;
- sem IAM corporativo completo;
- VPS real ainda pendente.

---

## Slide 12 — Conclusão

Mensagem:

> O resultado do projeto não é apenas um chatbot, mas uma arquitetura de referência para operar IA de forma controlada, observável e reproduzível.

Fechar distinguindo:
- o que foi demonstrado no laboratório;
- o que ainda precisa ser validado em deployment real e em experimentos de maior escala.
