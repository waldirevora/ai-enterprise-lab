# Agents, Skills e Tools

Este documento descreve o modelo de agentes atualmente implementado no AI Enterprise Lab.

## 1. Terminologia

No projeto atual, `skill` é uma forma conceitual de descrever uma capacidade do agente.

Não existe neste momento uma abstração de código independente chamada Skill Registry.

As capacidades concretas são implementadas por tools autorizadas e pela lógica de orquestração do agente.

## 2. Agente Enterprise Knowledge

Endpoint atual:

```text
POST /v1/agents/enterprise-knowledge/run
```

Ele exige autenticação Bearer e execução dentro do contexto autorizado do principal.

Exemplo:

```bash
curl -sS -X POST \
  http://127.0.0.1:8000/v1/agents/enterprise-knowledge/run \
  -H "Authorization: Bearer $AEL_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "message": "Summarize the authorized enterprise knowledge."
  }'
```

## 3. Request do agente

O contrato atual inclui:

```text
message
provider
external_approved
retrieval_limit
max_context_chunks
max_context_characters
temperature
```

`message` é obrigatório. Os demais campos possuem defaults ou são opcionais de acordo com o schema.

## 4. Resposta do agente

A resposta pode conter:

```text
answer
provider
backend
model
effective_classification
citations
tool_trace
steps_executed
tokens
duration
pricing / cost
```

O contrato atual registra entre 1 e 3 passos executados.

## 5. Tool atual

A principal tool de conhecimento empresarial implementada atualmente é:

```text
search_enterprise_knowledge
```

Ela consulta o RAG autorizado utilizando o contexto da organização e do principal.

## 6. Fronteiras de autorização

A tool recebe o escopo autorizado já derivado da autenticação e das regras de acesso.

Entre os elementos considerados estão organização, principal, classificações permitidas e grants de unidade organizacional aplicáveis.

O agente não deve ampliar esse escopo por conta própria.

## 7. Provider Policy

A escolha de provider continua sujeita às políticas do gateway.

Usar um provider externo não significa que conteúdo restrito está automaticamente autorizado a sair do ambiente local.

O campo `external_approved` participa explicitamente desse fluxo quando aplicável.

## 8. Tool trace

`tool_trace` permite observar quais ferramentas participaram da execução e apoia auditoria e troubleshooting.

Ele não substitui os controles de autorização no servidor.

## 9. Timeouts

O ambiente possui limites configuráveis para tools e geração de agentes:

```text
AGENT_TOOL_TIMEOUT_SECONDS
AGENT_GENERATION_TIMEOUT_SECONDS
```

Os valores utilizados devem ser ajustados pelo `.env`, sem alteração insegura do código para contornar timeouts.

## 10. Direção arquitetural

Novas tools devem seguir menor privilégio, validação de entrada, escopo explícito, tratamento de erros, observabilidade e testes antes de serem disponibilizadas aos agentes.
