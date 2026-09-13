# Local LLM Baseline

## Hardware

- Dell G7 7588
- Intel Core i5-8300H
- 32 GB RAM física
- WSL2 com aproximadamente 15 GB disponíveis
- NVIDIA GeForce GTX 1050 Ti 4 GB
- Ollama no Ubuntu/WSL2

## Providers lógicos

### local_fast

Modelo atual:

`qwen2.5-coder:3b`

Uso previsto:

- implementação localizada
- tarefas bem especificadas
- pequenas correções
- documentação
- testes simples
- agentes operacionais

### local_deep

Modelo atual:

`qwen2.5-coder:7b-instruct-q3_K_S`

Uso previsto:

- problemas locais mais difíceis
- debugging
- segunda tentativa local
- revisão adicional antes de recorrer à API externa

### external_deep

Provider previsto:

`DeepSeek API`

Estado padrão:

`desabilitado`

Uso previsto:

- arquitetura
- bugs difíceis
- mudanças amplas
- revisão crítica
- segurança
- tarefas que os modelos locais não resolvem satisfatoriamente

## Benchmark

| Métrica | local_fast | local_deep |
|---|---:|---:|
| Modelo | Qwen2.5-Coder 3B | Qwen2.5-Coder 7B Q3_K_S |
| Geração | 29.41 tok/s | 7.94 tok/s |
| Prompt | 254.76 tok/s | 112.32 tok/s |
| Contexto testado | 4096 | 4096 |
| Processamento | 100% GPU | 60% GPU / 40% CPU |
| VRAM aproximada | 3286 MiB | 3533 MiB |

## Decisão atual

`local_fast` é o modelo padrão do Dell.

`local_deep` é um modelo secundário usado quando maior capacidade local justificar menor velocidade.

`external_deep` somente pode ser utilizado quando a política permitir uso de API externa.

Nenhum provider recebe autoridade automática para alterar código ou executar ações sensíveis.

O fluxo continua sendo:

especificação → implementação → testes → revisão → git diff → auditoria → commit → PR