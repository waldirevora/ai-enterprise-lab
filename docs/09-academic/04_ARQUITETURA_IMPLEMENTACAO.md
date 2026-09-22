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
