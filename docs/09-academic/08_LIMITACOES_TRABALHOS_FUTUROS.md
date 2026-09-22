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

No A10, embedding, retrieval, geração `local_fast` e agente foram caracterizados com:

```text
1 warm-up excluído
5 execuções medidas
```

Essa amostra serve para caracterização inicial e reprodutibilidade local, não para estabelecer distribuição estatística robusta ou comparação definitiva de desempenho.

### 1.4 Dataset RAG

O estado atual usado nas medições contém:

```text
1 organização
1 documento
1 chunk
```

Por isso, a repetibilidade observada no retrieval não substitui:
- Hit@k;
- MRR;
- testes com ambiguidades;
- corpus com documentos concorrentes;
- avaliação de recall em escala.

### 1.5 Recursos de hardware não instrumentados

Ainda não foram registrados de forma acadêmica e sincronizada:
- CPU;
- RAM;
- VRAM;
- temperatura;
- energia.

Portanto, os resultados atuais medem principalmente latência e comportamento funcional.

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

1. Medir startup completo.
2. Caracterizar `local_deep` com protocolo controlado.
3. Coletar CPU, RAM e VRAM durante workloads.
4. Criar corpus RAG controlado maior.
5. Medir Hit@1, Hit@3, Hit@5 e MRR.
6. Executar teste acadêmico de logs/secrets com canários.
7. Consolidar resultados e discussão.
8. Fazer primeiro deployment manual em VPS.
9. Validar DNS público e ACME.
10. Automatizar deployment somente depois do processo manual validado.
11. Preparar demo e release v1.0.

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
