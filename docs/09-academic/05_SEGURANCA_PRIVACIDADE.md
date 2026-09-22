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
