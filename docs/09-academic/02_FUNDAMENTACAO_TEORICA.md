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
