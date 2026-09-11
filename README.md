# AI Enterprise Lab

Laboratório prático de arquitetura empresarial de IA local, desenvolvido para estudo de automação de processos, RAG, agentes, segurança, privacidade e integração opcional com modelos externos.

## Objetivo

Construir uma arquitetura de IA que priorize processamento local e privacidade, mantendo a possibilidade de utilizar APIs externas somente em tarefas previamente autorizadas.

## Princípios

- Privacy by design
- Security by design
- Local-first AI
- API externa desabilitada por padrão
- Secrets fora do código e do Git
- Menor privilégio
- Human-in-the-loop para ações sensíveis
- Auditoria e rastreabilidade
- Modelos substituíveis sem reescrever a aplicação

## Stack planejada

- Ubuntu 24.04 LTS via WSL2
- Python
- FastAPI
- PostgreSQL
- pgvector
- Docker
- Ollama
- LangGraph
- n8n
- Git e GitHub

## Estrutura planejada

```text
app/       aplicação e APIs
agents/    agentes e responsabilidades
rag/       ingestão, embeddings e retrieval
infra/     Docker e infraestrutura
tests/     testes automatizados
docs/      documentação
scripts/   scripts auxiliares
data/      dados controlados do laboratório
