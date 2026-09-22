# Limitações e Trabalhos Futuros

## 1. Limitações atuais

### 1.1 Hardware

O laboratório utiliza notebook com GPU de 4 GB de VRAM.

Isso limita:
- tamanho de modelos;
- concorrência;
- throughput;
- comparação de modelos maiores;
- fine-tuning local.

Os resultados quantitativos atuais são específicos desse ambiente.

### 1.2 Escala

A arquitetura foi validada em laboratório e em ambiente local equivalente a produção.

Não há evidência experimental de:
- carga empresarial;
- grande número de usuários;
- corpus RAG volumoso;
- concorrência significativa.

### 1.3 Amostra quantitativa

As principais caracterizações controladas utilizam amostras pequenas.

No A10, embeddings, retrieval, geração `local_fast` e agente foram caracterizados com:

```text
1 warm-up excluído
5 execuções medidas
```

Posteriormente, E01, E03, E05 e E08 também utilizaram séries controladas de 5 execuções ou ciclos.
O E14 utilizou 3 gerações sequenciais durante a fase `inference_load`.

Essas amostras são adequadas para caracterização inicial, reprodutibilidade local e identificação de comportamento do sistema, mas não estabelecem distribuição estatística robusta, capacidade em escala ou comparação definitiva de desempenho.

### 1.4 Dataset RAG

O baseline histórico A10 utilizava:

```text
1 organização
1 documento
1 chunk
```

O E06 ampliou a avaliação para 10 documentos sintéticos semanticamente distintos, 10 queries com ground truth conhecido e 1 documento persistente adicional como distractor.

Nesse corpus controlado foram medidos Hit@1, Hit@3, Hit@5 e MRR.

Apesar da ampliação, permanecem limitações importantes:
- corpus pequeno;
- documentos sintéticos;
- separação semântica relativamente clara;
- ausência de ambiguidades documentais fortes;
- ausência de corpus empresarial volumoso;
- ausência de avaliação de recall em escala;
- primeira execução formal com 10 queries, abaixo das 20 inicialmente planejadas.

Portanto, os resultados do E06 demonstram comportamento correto no corpus controlado, mas não permitem generalizar a qualidade de retrieval para bases empresariais grandes, densas ou ambíguas.

### 1.5 Caracterização de recursos

O E14 passou a registrar de forma sincronizada:
- CPU;
- RAM;
- utilização de GPU;
- VRAM;
- temperatura de GPU;
- RSS dos processos principais.

Permaneceram indisponíveis no ambiente utilizado:
- temperatura de CPU;
- potência e consumo energético.

A caracterização foi executada em WSL2 e a fase de carga utilizou apenas 3 gerações sequenciais com amostragem aproximada de 0,5 segundo.

O uso de `nvidia-smi` também introduz custo de observação.

Por isso, os resultados de recursos caracterizam este laboratório local e não constituem benchmark universal, estudo térmico completo ou estimativa de capacidade de produção em escala.

### 1.6 Alta disponibilidade

Não há:
- cluster PostgreSQL;
- Redis HA;
- múltiplas réplicas da aplicação;
- balanceamento distribuído;
- multi-region.

Esses elementos não são necessários para o objetivo da primeira versão, mas limitam conclusões sobre resiliência em escala.

### 1.7 IAM

O projeto possui autenticação e autorização próprias, mas não integra neste estágio:
- SSO corporativo;
- OIDC empresarial;
- SCIM;
- diretório corporativo.

### 1.8 Segurança

Os controles implementados reduzem riscos, mas não demonstram imunidade contra:
- todas as formas de prompt injection;
- supply-chain compromise;
- vulnerabilidades futuras;
- abuso por usuário autenticado com permissões excessivas;
- ataques distribuídos;
- comprometimento do host.

### 1.9 Agentes e tools

O endpoint atual não permite que o cliente escolha tools dinamicamente.

A tool `search_enterprise_knowledge` é selecionada server-side. Portanto, cenários de abuso por seleção arbitrária de tool via API não se aplicam à implementação atual.

Uma futura Tool Registry dinâmica exigirá novo modelo de autorização, sandbox e testes adversariais próprios.

### 1.10 Deployment real

O ambiente production-equivalent local foi validado, mas continuam pendentes:
- VPS real;
- DNS público;
- firewall do host real;
- ACME público;
- operação contínua na Internet;
- observação de logs e recursos em ambiente remoto.

---

## 2. Trabalhos futuros de curto prazo

1. Completar a caracterização do E02 `local_fast` com time-to-first-token, recursos e amostra formal maior.
2. Ampliar o E04 embeddings com throughput para múltiplos chunks e caracterização de recursos.
3. Consolidar o E07 ACL em uma matriz quantitativa acadêmica dos cenários já validados funcionalmente.
4. Decompor o E12 agents/tools em latência de embedding, retrieval, tool execution e geração.
5. Executar testes com carga concorrente e múltiplas requisições simultâneas.
6. Realizar o primeiro deployment manual em VPS real.
7. Validar DNS público, firewall do host, ACME, logs e recursos no ambiente remoto.
8. Automatizar o deployment somente depois da validação manual real.
9. Consolidar documentação acadêmica, apresentação e demo reproduzível.
10. Preparar e publicar a release v1.0 após os gates de encerramento.

---

## 3. FASE 30 — Continuous Deployment

A evolução de engenharia prevista é automatizar:
- build;
- release tag;
- migration gate;
- backup gate;
- deployment;
- health/readiness validation;
- rollback.

A automação deve ocorrer somente após o procedimento manual real estar validado.

---

## 4. Evolução em Harness Engineering

O projeto pode evoluir para estudar:
- orquestração de agentes;
- Tool Registry;
- execução isolada;
- sandbox;
- verificação;
- políticas de ferramenta;
- memória;
- tracing;
- avaliação automática;
- deployment gates;
- auditoria de ações.

---

## 5. Evolução em Forward Deployed Engineering

Uma implantação real permitiria estudar:
- discovery;
- requisitos reais;
- restrições do cliente;
- integração com sistemas existentes;
- governança;
- segurança contextual;
- adaptação da arquitetura;
- medição de valor operacional.

---

## 6. Possíveis extensões acadêmicas

- comparação RAG local vs provider externo;
- comparação de modelos locais;
- avaliação de quantização;
- avaliação de técnicas de chunking;
- hybrid search;
- reranking;
- avaliação automática de respostas;
- segurança de agentes;
- sandbox de tools;
- políticas adaptativas de provider;
- análise de cold start/warm state;
- benchmark com corpus de tamanhos progressivos.

---

## 7. Critério de encerramento da primeira versão

A primeira versão deve ser encerrada antes de incorporar extensões avançadas.

Critério:

```text
Local Functional Acceptance concluído
experimentos acadêmicos executados ou explicitamente justificados
resultados e limitações consolidados
VPS manual validado
documentação consolidada
demo reproduzível
release v1.0
```

Kubernetes, multi-region e outras extensões não são necessárias para o encerramento da versão acadêmica inicial.
