# Metodologia

## 1. Natureza da pesquisa

O projeto utiliza uma abordagem de **pesquisa aplicada**, com caráter **exploratório e experimental**, baseada na construção e validação de um artefato de software.

O objeto de estudo é uma arquitetura para aplicações empresariais de IA generativa. A avaliação ocorre por testes automatizados, experimentos controlados e observação de comportamento operacional.

---

## 2. Estratégia de desenvolvimento

O ciclo principal adotado foi:

```text
ENTENDER
→ DECIDIR
→ CONSTRUIR
→ VALIDAR
→ MEDIR
```

A estratégia foi complementada por quatro gates de engenharia.

### Antes da feature

1. Qual problema resolve?
2. Quem precisa disso?
3. Como funciona hoje?
4. Qual resultado é esperado?
5. Como será medido?

### Antes do código

1. Onde entra o dado?
2. Quem valida?
3. Onde fica a regra?
4. Onde o dado é armazenado?
5. Quem pode acessar?

### Depois do código

1. O que a feature faz?
2. Quais são entradas e saídas?
3. Como pode falhar?
4. Como foi testada?
5. Existe risco de segurança?
6. O que mudou no Git?

### Depois do deployment

1. Está funcionando?
2. Está sendo utilizado?
3. Melhorou o problema?
4. Quanto melhorou?
5. O que precisa mudar?

---

## 3. Desenvolvimento incremental

O sistema foi construído em fases incrementais. Cada fase adicionou controles ou capacidades e foi integrada por branch, Pull Request, CI e merge.

Entre as fases concluídas estão:
- hardening de segurança;
- revisão de privacidade;
- CI;
- agentes e orquestração;
- observabilidade;
- runtime e deployment de produção.

A FASE 29 consolidou a infraestrutura de produção e foi integrada ao branch `main` pelo PR #18.

---

## 4. Ambiente experimental

### Hardware local

Notebook utilizado como laboratório:

```text
Dell G7 7588
RAM: 32 GB
GPU: NVIDIA GTX 1050 Ti 4 GB
SSD: 512 GB + 1 TB
```

### Componentes

```text
FastAPI
Python 3.12
PostgreSQL 17 + pgvector
Redis 8
n8n
Docker / Docker Compose
Caddy
Ollama
```

### Modelos locais planejados/atuais

```text
local_fast:
qwen2.5-coder:3b

local_deep:
qwen2.5-coder:7b-instruct-q3_K_S

embedding:
qwen3-embedding:0.6b
```

O provedor externo é opcional e controlado por política.

---

## 5. Estratégia de validação

A validação é dividida em quatro níveis.

### 5.1 Testes automatizados

Suíte atual:

```text
424 testes aprovados
```

Categorias presentes no projeto incluem:
- autenticação;
- autorização;
- RAG;
- agentes;
- rate limiting;
- auditoria;
- observabilidade;
- segurança;
- readiness;
- migrations;
- deployment contracts.

### 5.2 Validação de integração

Testa interação entre:
- FastAPI;
- PostgreSQL;
- Redis;
- Caddy;
- n8n;
- migrations.

### 5.3 Validação production-equivalent local

Foi executada uma topologia equivalente à produção no notebook, com:
- imagem imutável;
- PostgreSQL;
- Redis;
- app;
- Caddy;
- n8n;
- TLS interno;
- migrations explícitas;
- readiness;
- falha e recuperação de Redis.

### 5.4 Local Functional Acceptance

Etapa acadêmica ainda pendente de conclusão.

Deverá validar:
- Ollama real;
- embeddings reais;
- ingestão RAG;
- consulta RAG;
- geração local;
- agentes;
- persistência;
- restart;
- backup e restore;
- métricas de desempenho.

---

## 6. Controle de mudanças

O projeto utiliza:
- Git;
- branches de feature;
- Conventional Commits;
- Pull Requests;
- CI;
- revisão antes de commit;
- revisão antes de merge.

O trabalho de produção da FASE 29 foi integrado no commit de `main`:

```text
eee0ede3ad09c3113fad1757db9eb14cd0270d41
```

---

## 7. Critérios de qualidade

Uma mudança não é considerada concluída apenas por compilar.

Os critérios incluem:
- testes;
- segurança;
- controle de acesso;
- comportamento de falha;
- compatibilidade com operação;
- logs sem segredos;
- documentação;
- recuperação;
- consistência de migrations.

---

## 8. Procedimento experimental

Cada experimento deverá registrar:

```text
ID do experimento
data/hora
commit testado
hardware
configuração do modelo
entrada
procedimento
métrica
resultado
observações
limitações
```

Experimentos devem ser repetidos no mesmo ambiente quando houver comparação de desempenho.

---

## 9. Tratamento dos resultados

Os resultados serão classificados como:
- aprovado;
- reprovado;
- inconclusivo;
- não executado.

Métricas numéricas devem apresentar:
- quantidade de execuções;
- média;
- mediana quando aplicável;
- mínimo;
- máximo;
- desvio ou variação quando relevante.

O projeto deve evitar falsa precisão em amostras pequenas.

---

## 10. Reprodutibilidade

A reprodutibilidade é apoiada por:
- dependências versionadas;
- Dockerfile;
- Compose;
- migrations;
- scripts de preflight;
- scripts de backup;
- testes;
- documentação operacional;
- commit identificável.

A execução de experimentos acadêmicos deverá sempre registrar o hash do commit usado.
