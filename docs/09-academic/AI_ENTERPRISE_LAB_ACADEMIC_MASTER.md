# AI ENTERPRISE LAB — DOCUMENTAÇÃO ACADÊMICA MASTER
## Documento consolidado

Este arquivo consolida os principais documentos acadêmicos do projeto. Os arquivos individuais em `docs/09-academic/` devem ser usados como fonte canônica durante a evolução do trabalho.


---

# AI Enterprise Lab: Arquitetura Local e Privada para Aplicações Corporativas com RAG, Agentes de IA, Segurança e Observabilidade

## Identificação

**Autor:** Waldir Évora<br>
**Projeto:** AI Enterprise Lab<br>
**Área:** Inteligência Artificial e Automação Digital<br>
**Natureza:** Projeto acadêmico aplicado / arquitetura de referência<br>
**Instituição:** PREENCHER<br>
**Disciplina:** PREENCHER<br>
**Professor(a):** PREENCHER<br>
**Período:** PREENCHER<br>

---

## 1. Resumo

A adoção de modelos de linguagem de grande porte em ambientes corporativos introduz benefícios relacionados à automação, recuperação de conhecimento e apoio à tomada de decisão, mas também cria desafios de privacidade, controle de acesso, rastreabilidade, observabilidade, integração com sistemas existentes e confiabilidade operacional.

O **AI Enterprise Lab** propõe e implementa uma arquitetura de referência para aplicações corporativas de inteligência artificial generativa com execução local ou controlada, combinando APIs, Retrieval-Augmented Generation (RAG), agentes de IA, persistência estruturada, autorização, auditoria, rate limiting, observabilidade e mecanismos de deployment. A solução foi construída com FastAPI, PostgreSQL com suporte vetorial, Redis, n8n, Ollama, Docker e componentes adicionais de segurança e operação.

A proposta não busca criar apenas uma interface conversacional. O objetivo é estudar como diferentes mecanismos de engenharia podem ser combinados para produzir uma aplicação de IA mais controlável, verificável e adequada a cenários empresariais. A arquitetura adota princípios como *deny-by-default*, segregação entre serviços, uso de variáveis de ambiente protegidas, controle de acesso por organização e unidade organizacional, ACL de documentos, migrations verificáveis, health/readiness checks, backups e rollback operacional.

Até o estágio atual, o projeto possui uma suíte automatizada com 427 testes aprovados, imagem de aplicação executada como usuário não privilegiado, Redis executado sem privilégios de root, pipelines de CI, políticas de readiness, framework de migrations, estratégia de backup e recuperação e topologia de produção validada em ambiente local equivalente. A caracterização acadêmica já inclui medições controladas de startup, geração `local_deep`, ingestão e retrieval RAG, recuperação do Redis, inspeção de logs/secrets e uso de CPU, RAM, GPU e VRAM. Permanecem como extensões a caracterização complementar de E02, E04, E07 e E12, testes de carga concorrente e validação em VPS pública real.

**Palavras-chave:** Inteligência Artificial Generativa; RAG; Agentes de IA; LLM; Privacidade; Segurança; Observabilidade; FastAPI; PostgreSQL; Docker.

---

## 2. Introdução

Modelos de linguagem de grande porte passaram a ser utilizados em tarefas de geração textual, análise de documentos, suporte a processos, automação e interação com sistemas. Entretanto, a utilização desses modelos em contexto empresarial exige mais do que a capacidade de gerar respostas. Informações corporativas podem possuir restrições de acesso, dados sensíveis, requisitos de auditoria e dependências operacionais que não estão presentes em demonstrações simples de IA generativa.

Nesse contexto, surgem questões relacionadas a onde os dados são processados, como documentos são recuperados, quem pode acessar determinada informação, como as chamadas de modelos são auditadas, o que ocorre quando um componente fica indisponível e como uma nova versão da aplicação é implantada ou revertida.

O AI Enterprise Lab foi desenvolvido como ambiente prático para explorar essas questões. O projeto combina IA local, RAG, agentes, APIs, persistência, mecanismos de segurança e infraestrutura conteinerizada. O laboratório também funciona como plataforma de aprendizagem de engenharia de software aplicada a IA, aproximando conceitos de backend, integração, segurança e operações.

---

## 3. Problema de pesquisa

Aplicações simples de IA generativa podem funcionar adequadamente em demonstrações controladas, mas apresentam limitações quando precisam manipular conhecimento corporativo, integrar ferramentas, respeitar autorização, registrar ações e operar de maneira previsível.

Dessa forma, o problema de pesquisa adotado é:

> **Como estruturar e validar uma arquitetura local e privada de inteligência artificial generativa capaz de integrar RAG, agentes, APIs, controle de acesso, persistência, segurança e observabilidade, mantendo rastreabilidade e condições de implantação empresarial?**

---

## 4. Hipótese de trabalho

A hipótese adotada é que uma arquitetura modular, com separação entre aplicação, dados, cache, orquestração, modelos e camada de entrada, combinada a controles explícitos de autorização, auditoria, migrations e health/readiness, pode oferecer maior governança e previsibilidade operacional do que uma aplicação monolítica centrada exclusivamente no modelo de linguagem.

A hipótese será avaliada por evidências técnicas e experimentais. O projeto não pretende demonstrar que a arquitetura é universalmente superior a todas as alternativas, mas verificar se ela atende aos requisitos definidos para o laboratório.

---

## 5. Objetivo geral

Projetar, implementar e validar uma arquitetura de referência para aplicações empresariais de inteligência artificial generativa com execução local ou controlada, integrando RAG, agentes, APIs, segurança, persistência e observabilidade.

---

## 6. Objetivos específicos

1. Implementar uma API central para mediação das funcionalidades de IA.
2. Permitir execução de modelos locais e uso controlado de provedor externo.
3. Implementar ingestão e recuperação de documentos por RAG.
4. Restringir acesso aos documentos por contexto organizacional e ACL.
5. Implementar mecanismos de agentes e ferramentas com políticas de execução.
6. Adotar autenticação, autorização e princípio *deny-by-default*.
7. Registrar eventos relevantes para auditoria.
8. Implementar rate limiting com dependência de Redis.
9. Diferenciar liveness e readiness da aplicação.
10. Implementar migrations verificáveis e reproduzíveis.
11. Definir procedimentos de backup, rollback e recuperação.
12. Empacotar a aplicação em imagem Docker não privilegiada.
13. Definir topologia de implantação com proxy reverso e TLS.
14. Automatizar testes e verificações por CI.
15. Medir desempenho, recuperação de informação, resiliência e consumo de recursos no ambiente local.

---

## 7. Justificativa

A relevância do projeto está na distância existente entre demonstrações de IA generativa e sistemas adequados a processos organizacionais. Em ambientes empresariais, uma resposta correta do modelo não é o único critério de qualidade. Também são relevantes controle de acesso, confidencialidade, rastreabilidade, recuperação de falhas, observabilidade e repetibilidade da implantação.

O uso de RAG permite combinar o conhecimento paramétrico do modelo com fontes externas recuperadas durante a inferência. A literatura demonstra o potencial dessa abordagem para tarefas intensivas em conhecimento. Entretanto, o uso corporativo de RAG introduz desafios adicionais, como segregação documental e garantia de que a recuperação respeite permissões.

Agentes ampliam o problema porque um modelo passa a poder acionar ferramentas e produzir efeitos em sistemas. Por isso, o projeto trata execução de ferramentas como uma fronteira de segurança e não como simples extensão do prompt.

A utilização de modelos locais também é relevante em cenários nos quais privacidade, custo, latência ou autonomia operacional influenciam a escolha tecnológica.

---

## 8. Escopo

### 8.1 Incluído

- FastAPI como gateway de aplicação;
- PostgreSQL e pgvector;
- Redis;
- n8n;
- Ollama e modelos locais;
- provedor externo opcional e controlado;
- RAG;
- agentes;
- autenticação e autorização;
- organizações e unidades organizacionais;
- ACL documental;
- rate limiting;
- auditoria;
- observabilidade;
- health/readiness;
- Docker;
- Caddy;
- migrations;
- backup e recuperação;
- CI;
- deployment manual documentado.

### 8.2 Fora do escopo da primeira versão

- Kubernetes;
- autoscaling;
- multi-region;
- alta disponibilidade distribuída;
- blue/green deployment;
- IAM corporativo completo;
- SaaS multiempresa comercial;
- treinamento de modelo fundacional;
- fine-tuning em larga escala;
- substituição de mecanismos determinísticos por LLM.

---

## 9. Questões de avaliação

O trabalho deverá responder empiricamente:

1. O laboratório consegue executar o fluxo completo de RAG localmente?
2. A recuperação respeita corretamente ACL e contexto organizacional?
3. O sistema diferencia corretamente liveness de readiness?
4. A indisponibilidade do Redis degrada readiness sem derrubar liveness?
5. Dados e migrations permanecem consistentes após reinicializações?
6. O backup produzido pode ser restaurado em ambiente limpo?
7. A execução local apresenta consumo de recursos compatível com o notebook utilizado?
8. Qual é a latência dos diferentes perfis de modelo?
9. Os agentes respeitam as políticas de ferramentas estabelecidas?
10. Os mecanismos de auditoria e observabilidade registram eventos esperados sem expor segredos?

---

## 10. Contribuição esperada

A contribuição principal é uma arquitetura de referência implementada e validada, acompanhada de documentação técnica e experimental. O valor acadêmico está na integração de diferentes disciplinas — IA generativa, recuperação de informação, backend, segurança, observabilidade e operações — em um único sistema experimental.

O projeto também produz evidências reproduzíveis por meio de testes automatizados, scripts operacionais, migrations versionadas e experimentos definidos.

---

## 11. Organização sugerida do trabalho final

1. Introdução
2. Fundamentação teórica
3. Metodologia
4. Arquitetura proposta
5. Implementação
6. Segurança, privacidade e governança
7. Experimentos e validação
8. Resultados e discussão
9. Limitações e trabalhos futuros
10. Conclusão
11. Referências
12. Apêndices

---

# Fundamentação Teórica

## 1. Modelos de linguagem e aplicações empresariais

Modelos de linguagem de grande porte são capazes de executar tarefas de geração, transformação e análise de linguagem natural. Em aplicações empresariais, entretanto, o modelo é apenas um componente de um sistema maior. A qualidade da solução depende de mecanismos que definem quais dados podem ser acessados, quais ferramentas podem ser utilizadas, como o resultado é registrado e como falhas são tratadas.

O AI Enterprise Lab adota essa perspectiva sistêmica: o modelo não é tratado como autoridade independente, mas como componente subordinado às regras da aplicação.

---

## 2. Retrieval-Augmented Generation

Retrieval-Augmented Generation combina geração neural com recuperação de conhecimento externo. Lewis et al. (2020) formalizaram uma arquitetura que combina memória paramétrica e memória não paramétrica, permitindo que a geração seja condicionada por documentos recuperados.

No contexto deste projeto, o conceito é aplicado por meio de:
- ingestão de documentos;
- segmentação;
- geração de embeddings;
- persistência vetorial;
- busca semântica;
- construção de contexto;
- geração condicionada ao conteúdo recuperado.

A diferença relevante para o contexto empresarial é que a recuperação não deve considerar apenas similaridade. O documento também precisa ser elegível de acordo com autorização, organização, unidade organizacional e ACL.

Assim, o fluxo conceitual é:

```text
consulta
→ contexto de acesso
→ filtros de autorização
→ busca vetorial
→ documentos elegíveis
→ construção de contexto
→ geração
```

Essa sequência reduz o risco de recuperar um documento proibido e tentar removê-lo posteriormente.

---

## 3. Recuperação densa e embeddings

Busca semântica utiliza representações vetoriais para aproximar consultas e documentos por similaridade no espaço de embeddings. Técnicas de recuperação densa ganharam relevância em sistemas de pergunta e resposta e compõem a base de muitas implementações modernas de RAG.

No laboratório, embeddings são gerados localmente e armazenados em PostgreSQL com extensão vetorial. Essa escolha permite manter metadados relacionais, regras de acesso e vetores no mesmo sistema de persistência.

A avaliação experimental deve considerar não apenas latência, mas também relevância dos documentos recuperados.

---

## 4. Agentes de IA e uso de ferramentas

Agentes de IA diferem de uma chamada simples ao modelo porque podem executar um ciclo em que o modelo seleciona ações, usa ferramentas e incorpora resultados intermediários. Trabalhos como ReAct demonstram a combinação entre raciocínio e ação em ambientes externos.

Em sistemas corporativos, essa capacidade aumenta o potencial de automação, mas também amplia a superfície de risco. Uma ferramenta pode consultar banco de dados, chamar APIs ou disparar automações. Portanto, a autorização de ferramentas deve ocorrer na camada da aplicação.

O AI Enterprise Lab adota:
- catálogo explícito de ferramentas;
- políticas por provider e contexto;
- *deny-by-default*;
- validação server-side;
- auditoria de ações;
- ausência de confiança automática em instruções geradas pelo modelo.

---

## 5. IA local e privacidade

A execução local de modelos pode reduzir a necessidade de transmissão de determinados dados para serviços externos. Isso não elimina riscos: um sistema local ainda pode possuir falhas de autenticação, logs inadequados, permissões excessivas ou exposição de portas.

Por isso, “local” não é utilizado como sinônimo de “seguro”. O projeto combina processamento local com controles tradicionais de engenharia de segurança.

A arquitetura também permite um provedor externo controlado. A política define quando o egress é permitido, evitando que a seleção de um provedor externo seja consequência automática de uma solicitação do usuário.

---

## 6. Segurança de aplicações de IA generativa

Aplicações com LLMs adicionam riscos específicos aos riscos tradicionais de aplicações web. O OWASP Top 10 for LLM Applications 2025 inclui categorias como prompt injection, sensitive information disclosure, supply chain, data/model poisoning e improper output handling.

O projeto trata especialmente:
- prompt e dados externos como conteúdo não confiável;
- segregação de dados;
- saída do modelo como conteúdo que ainda precisa de validação;
- controle explícito de ferramentas;
- proteção de segredos;
- minimização de logs;
- gestão de dependências.

Também permanecem aplicáveis riscos tradicionais de aplicações web, como controle de acesso quebrado, configuração insegura, falhas na cadeia de suprimentos, autenticação e logging insuficiente.

---

## 7. Gestão de risco em IA

O NIST AI Risk Management Framework propõe uma abordagem para gestão de riscos de sistemas de IA ao longo de seu ciclo de vida. O Generative AI Profile complementa o framework com riscos específicos de IA generativa.

O AI Enterprise Lab não afirma conformidade formal com o NIST AI RMF. Entretanto, utiliza princípios compatíveis com a ideia de mapear, medir e gerenciar riscos, por meio de:
- inventário de componentes;
- políticas explícitas;
- testes;
- auditoria;
- observabilidade;
- documentação de limitações;
- validação antes de deployment.

---

## 8. Observabilidade

Observabilidade em uma aplicação de IA permite responder perguntas sobre o comportamento interno do sistema a partir de sinais como métricas, logs e eventos.

O laboratório diferencia:
- métricas de infraestrutura;
- métricas de requisição;
- métricas relacionadas a geração;
- métricas de RAG;
- eventos de rate limiting;
- eventos de auditoria;
- liveness;
- readiness.

Uma característica importante é a separação entre “processo vivo” e “serviço pronto para receber tráfego”. A aplicação pode continuar viva mesmo se uma dependência necessária para determinadas operações estiver temporariamente indisponível.

---

## 9. Confiabilidade e readiness

Liveness responde se o processo da aplicação está operacional. Readiness responde se o serviço possui as dependências necessárias para atender adequadamente.

No projeto:
- PostgreSQL é dependência obrigatória de readiness;
- Redis é dependência de readiness quando o rate limiting está habilitado;
- falha do Redis não deve transformar automaticamente liveness em falha;
- recuperação da dependência deve restaurar readiness.

Esse comportamento já foi validado em ambiente local equivalente a produção.

---

## 10. Persistência, migrations e evolução de schema

Sistemas persistentes precisam evoluir o schema sem depender de operações manuais não rastreadas.

O framework de migrations do projeto registra:
- versão;
- nome;
- checksum;
- data de aplicação.

Também valida o baseline histórico e utiliza advisory lock para impedir execução concorrente de migrations.

Essa abordagem permite detectar:
- migration alterada após aplicação;
- gaps de versão;
- schema incompatível;
- execução concorrente.

---

## 11. Conteinerização e princípio do menor privilégio

O uso de containers favorece repetibilidade, mas não garante segurança por si só.

O projeto aplica:
- imagem com versão base fixada;
- usuário não-root para a aplicação;
- Redis não-root;
- root filesystem read-only para componentes selecionados;
- `no-new-privileges`;
- redução de capabilities;
- separação de redes;
- não publicação de PostgreSQL, Redis e FastAPI diretamente no host em produção.

O proxy reverso atua como borda pública.

---

## 12. Síntese conceitual

A fundamentação do projeto pode ser resumida em seis ideias:

```text
conhecimento externo → RAG
ações externas       → agentes + tools
dados corporativos   → autorização + ACL
IA local             → privacidade + autonomia
operação             → observabilidade + readiness
evolução             → migrations + CI + deployment controlado
```

O AI Enterprise Lab investiga a integração dessas ideias em uma arquitetura única e reproduzível.

---

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
427 testes aprovados
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

---

## Protocolos experimentais complementares E01–E14

Após a caracterização A10, foram executados experimentos complementares para reduzir lacunas da primeira versão acadêmica.
Os resultados são caracterizações locais do laboratório e não devem ser tratados como benchmarks universais.

### E01 — Startup

Foram executados 5 ciclos controlados de startup, preservando os volumes persistentes.

A condição principal de prontidão foi PostgreSQL e Redis saudáveis, com `/ready=200`.
O n8n foi acompanhado separadamente como serviço auxiliar.

### E03 — Geração `local_deep`

O protocolo utilizou 1 warm-up excluído e 5 execuções sequenciais medidas.
A temperatura foi fixada em 0, com `max_output_tokens=64` e contexto de 4096 tokens.

Modelo avaliado: `qwen2.5-coder:7b-instruct-q3_K_S`.

### E05 — Ingestão RAG

O E05 caracterizou o pipeline de ingestão sem misturar a avaliação de ACL, que permanece no E07.
Foram medidos 5 documentos após 1 warm-up excluído.
Cada documento continha 1000 palavras e produziu 6 chunks com `chunk_size_words=220` e `overlap_words=40`.
Cada execução incluiu chunking, embeddings, persistência em PostgreSQL/pgvector e cleanup posterior.

### E06 — Qualidade de retrieval

Foi utilizado um corpus sintético controlado com 10 documentos semanticamente distintos e 10 queries com ground truth definido previamente.
Um documento persistente adicional permaneceu como distractor, com 1 chunk por documento temporário e `limit=20`.
Foram calculados Hit@1, Hit@3, Hit@5 e MRR.
O planejamento inicial previa pelo menos 20 perguntas, mas esta primeira execução formal utilizou 10 queries; essa redução permanece registrada como limitação metodológica.

### E08 — Redis recovery

Foram executados 5 ciclos controlados com Redis disponível, indisponível e posteriormente recuperado.
Durante a falha, `/health=200` e `/ready=503`; após o restart do Redis, foi medido o tempo até `/ready=200`.
A API FastAPI não foi reiniciada entre falha e recuperação.

### E13 — Logs e secrets

Foram utilizados somente canários sintéticos para verificar audit metadata, Authorization, headers, query strings, respostas HTTP e access logs reais do Uvicorn.
O finding identificado no access log foi corrigido e o mesmo canário foi repetido como teste de regressão.

### E14 — Recursos do sistema

A caracterização foi executada em WSL2 nas fases `cold_idle`, `loaded_idle` e `inference_load`.
A amostragem utilizou `/proc/stat`, `/proc/meminfo`, `/proc/<pid>` e `nvidia-smi`, em intervalo aproximado de 0,5 segundo.
A temperatura de CPU não ficou disponível no WSL2; a temperatura da GPU foi obtida por `nvidia-smi`.
Os resultados representam caracterização local deste hardware e desta configuração, não benchmark universal.

---

# Arquitetura e Implementação

## 1. Visão geral

A arquitetura separa aplicação, persistência, cache, automação, modelos e borda HTTP.

```text
Cliente
  |
  v
Caddy / TLS
  |
  v
FastAPI Gateway
  |
  +---------------------+
  |                     |
  v                     v
PostgreSQL            Redis
+ pgvector            rate limiting
  |
  +-------------------------+
  |                         |
  v                         v
RAG / ACL               Audit / metrics
  |
  v
Provider Policy
  |
  +----------------------+----------------------+
  |                      |                      |
  v                      v                      v
local_fast            local_deep          external_deep
Ollama                Ollama              provider externo

n8n atua como camada de automação assíncrona quando necessário.
```

---

## 2. FastAPI Gateway

O gateway centraliza:
- autenticação;
- autorização;
- políticas de provider;
- chamadas de geração;
- endpoints RAG;
- agentes;
- rate limiting;
- readiness;
- auditoria;
- observabilidade.

Essa centralização evita que clientes internos acessem diretamente os modelos ou bancos.

---

## 3. PostgreSQL e pgvector

PostgreSQL armazena:
- dados de aplicação;
- entidades organizacionais;
- permissões;
- documentos;
- metadados;
- chunks;
- vetores;
- ACL;
- dados de auditoria conforme o desenho da aplicação.

A extensão vetorial permite consulta por similaridade sem introduzir um banco vetorial separado no laboratório.

---

## 4. Redis

Redis é utilizado para rate limiting e funções de suporte operacional.

Em produção:
- não possui porta publicada no host;
- exige autenticação;
- executa como usuário não-root;
- é considerado dependência de readiness quando o limiter está habilitado.

---

## 5. n8n

n8n fornece uma camada de automação e integração.

No desenho de produção:
- não é exposto publicamente;
- utiliza binding de loopback no host;
- possui banco próprio dentro do PostgreSQL;
- utiliza chave de criptografia que deve ser preservada separadamente dos dumps.

---

## 6. Ollama e providers

A aplicação utiliza abstração de providers.

Perfis:

```text
local_fast
local_deep
external_deep
```

A seleção do provider é condicionada por política.

O objetivo é permitir:
- baixo custo;
- privacidade;
- execução offline em determinados fluxos;
- uso externo somente quando autorizado.

---

## 7. RAG

Pipeline lógico:

```text
documento
→ validação
→ autorização de ingestão
→ extração/segmentação
→ embedding
→ persistência
→ consulta
→ filtro de autorização
→ busca vetorial
→ construção de contexto
→ geração
```

O controle de acesso ocorre antes de o conteúdo ser disponibilizado ao modelo.

---

## 8. Agentes

Agentes utilizam:
- schemas definidos;
- runtime controls;
- ferramentas registradas;
- políticas;
- auditoria.

A arquitetura não permite que o LLM defina unilateralmente quais operações são autorizadas.

---

## 9. Autorização

O modelo de acesso inclui:
- tenant/organização;
- unidades organizacionais;
- grants;
- escopo;
- ACL documental.

A política dominante é *deny-by-default*.

---

## 10. Readiness

Readiness verifica dependências necessárias para atendimento adequado.

O projeto validou:
- PostgreSQL disponível → readiness normal;
- Redis disponível quando limiter habilitado → readiness normal;
- Redis indisponível → readiness 503;
- liveness permanece 200;
- recuperação de Redis → readiness retorna a 200.

---

## 11. Migrations

O framework possui CLI:

```text
python -m app.db.migrations verify
python -m app.db.migrations baseline
python -m app.db.migrations status
python -m app.db.migrations apply
```

Metadados registrados:

```text
version
name
checksum_sha256
applied_at
```

O runner utiliza advisory lock para impedir concorrência.

---

## 12. Runtime Docker

A imagem:
- usa Python 3.12;
- possui base fixada por digest;
- instala somente dependências runtime;
- executa como UID/GID 10001;
- inclui CLI de migrations;
- não inclui segredos no build context.

---

## 13. Topologia de produção

Princípios:

```text
Caddy:
80/443 públicos

FastAPI:
somente rede interna

PostgreSQL:
somente rede interna

Redis:
somente rede interna

n8n:
loopback no host
```

A aplicação aceita forwarded headers somente do endereço do Caddy definido na rede de borda.

---

## 14. Backup e recuperação

O script de backup gera dumps em formato custom do PostgreSQL para:
- aplicação;
- banco do n8n.

Também produz:
- checksums;
- manifest;
- metadados de versão.

Permissões restritivas são aplicadas ao diretório e arquivos de backup.

A chave de criptografia do n8n precisa ser preservada fora do dump.

---

## 15. CI

O pipeline executa em Python 3.12 e inclui:
- instalação do lock;
- `pip check`;
- `compileall`;
- `pytest`;
- `pip-audit`.

O PR #18 foi aprovado pelo CI antes do merge.

---

## 16. Estado arquitetural

A arquitetura de código e produção está consolidada.

A próxima validação necessária é funcional, usando o Ollama real do notebook e os fluxos de RAG/agentes, seguida de coleta de métricas acadêmicas.

---

# Segurança, Privacidade e Governança

## 1. Princípios

O projeto adota:

```text
deny-by-default
least privilege
server-side validation
explicit trust boundaries
no secrets in logs
no secrets in Git
auditable actions
controlled provider egress
```

---

## 2. Ameaças consideradas

### Aplicação tradicional

- broken access control;
- falhas de autenticação;
- misconfiguration;
- injeção;
- exposição de segredos;
- dependências vulneráveis;
- logging insuficiente.

### Aplicações de IA generativa

- prompt injection;
- sensitive information disclosure;
- improper output handling;
- supply chain;
- data poisoning;
- excessive agency;
- exposição indevida de ferramentas.

---

## 3. Controle de acesso

O controle de acesso é aplicado na camada da aplicação.

O sistema considera:
- identidade;
- organização;
- unidade organizacional;
- grants;
- escopo;
- ACL documental.

Um documento não deve ser recuperado para um usuário que não possua autorização, ainda que apresente alta similaridade vetorial.

---

## 4. Segredos

Segredos reais:
- não são versionados;
- não são incluídos na imagem;
- não são impressos em logs;
- são carregados por environment no runtime.

O production env é mantido fora do repositório, com permissão esperada `0600`.

O template versionável contém somente nomes e valores não sensíveis.

---

## 5. Providers externos

O uso de provedor externo é uma decisão de política.

O modelo não pode decidir sozinho enviar dados para um endpoint externo.

O sistema pode bloquear egress por padrão e permitir apenas cenários explicitamente aprovados.

---

## 6. Segurança de containers

Aplicação:
```text
non-root
read-only root filesystem
no-new-privileges
cap_drop=ALL
```

Redis:
```text
non-root
sem porta publicada no host
```

Caddy:
```text
read-only root filesystem
no-new-privileges
cap_drop=ALL
CAP_NET_BIND_SERVICE
```

---

## 7. Fronteira de proxy

Somente Caddy atua como borda pública.

Forwarded headers são aceitos somente do proxy conhecido. Essa decisão reduz risco de spoofing de origem quando cabeçalhos são enviados diretamente por cliente não confiável.

---

## 8. Auditoria

Eventos relevantes devem registrar contexto suficiente para investigação sem copiar segredos ou conteúdo sensível desnecessário.

Exemplos:
- autenticação;
- autorização negada;
- política de provider;
- rate limit;
- uso de agente;
- acesso RAG;
- falhas relevantes.

---

## 9. Dependências

A cadeia de suprimentos é controlada por:
- locks;
- versões fixadas;
- CI;
- `pip check`;
- `pip-audit`;
- revisão antes de merge.

No fechamento da FASE 29, os locks de runtime e desenvolvimento foram auditados com `pip-audit 2.10.1` sem vulnerabilidades conhecidas no momento da execução.

Esse resultado é temporal e não garante ausência futura de vulnerabilidades.

---

## 10. Limitações

O projeto não afirma:
- conformidade certificada com NIST;
- conformidade formal com ISO;
- ausência total de vulnerabilidades;
- proteção contra todos os tipos de prompt injection;
- isolamento equivalente a ambiente de alta segurança.

O laboratório implementa controles inspirados em boas práticas e validações técnicas, mas uma implantação empresarial real exige avaliação de risco contextual.

---

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

---

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

---

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

---

# Referências

> Ajustar a formatação final às normas exigidas pela instituição, por exemplo ABNT NBR 6023.

## Referências acadêmicas e normativas

LEWIS, Patrick et al. **Retrieval-Augmented Generation for Knowledge-Intensive NLP Tasks**. Advances in Neural Information Processing Systems, v. 33, p. 9459–9474, 2020. Disponível em: https://arxiv.org/abs/2005.11401.

KARPUKHIN, Vladimir et al. **Dense Passage Retrieval for Open-Domain Question Answering**. Proceedings of EMNLP, 2020.

GUU, Kelvin et al. **REALM: Retrieval-Augmented Language Model Pre-Training**. Proceedings of ICML, 2020. Disponível em: https://arxiv.org/abs/2002.08909.

IZACARD, Gautier et al. **Atlas: Few-shot Learning with Retrieval Augmented Language Models**. Journal of Machine Learning Research / arXiv, 2022. Disponível em: https://arxiv.org/abs/2208.03299.

YAO, Shunyu et al. **ReAct: Synergizing Reasoning and Acting in Language Models**. 2022. Disponível em: https://arxiv.org/abs/2210.03629.

TABASSI, Elham. **Artificial Intelligence Risk Management Framework (AI RMF 1.0)**. Gaithersburg: National Institute of Standards and Technology, 2023. NIST AI 100-1. DOI: 10.6028/NIST.AI.100-1.

NATIONAL INSTITUTE OF STANDARDS AND TECHNOLOGY. **Artificial Intelligence Risk Management Framework: Generative Artificial Intelligence Profile**. NIST AI 600-1, 2024.

OWASP FOUNDATION. **OWASP Top 10 for LLM Applications 2025**. 2024/2025. Disponível em: https://genai.owasp.org/llm-top-10/.

OWASP FOUNDATION. **OWASP Top 10:2025**. Disponível em: https://top10.owasp.org/2025/.

## Referências técnicas do projeto

FASTAPI. **FastAPI Documentation**. Disponível em: https://fastapi.tiangolo.com/.

POSTGRESQL GLOBAL DEVELOPMENT GROUP. **PostgreSQL Documentation**. Disponível em: https://www.postgresql.org/docs/.

PGVECTOR. **pgvector: Open-source vector similarity search for Postgres**. Disponível em: https://github.com/pgvector/pgvector.

REDIS. **Redis Documentation**. Disponível em: https://redis.io/docs/.

DOCKER. **Docker Documentation**. Disponível em: https://docs.docker.com/.

CADDY. **Caddy Documentation**. Disponível em: https://caddyserver.com/docs/.

OLLAMA. **Ollama Documentation**. Disponível em: https://ollama.com/.

N8N. **n8n Documentation**. Disponível em: https://docs.n8n.io/.

PROMETHEUS. **Prometheus Documentation**. Disponível em: https://prometheus.io/docs/.

## Nota

As referências técnicas documentam componentes específicos de implementação. As referências acadêmicas e normativas fundamentam os conceitos, riscos e critérios de arquitetura utilizados no texto.

---

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
