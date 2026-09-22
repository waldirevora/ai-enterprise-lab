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
