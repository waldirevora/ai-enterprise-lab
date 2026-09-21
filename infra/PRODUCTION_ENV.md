# Production Environment

O ambiente de produção não usa o `.env` local do repositório.

## Arquivos

Template versionado: `infra/.env.prod.example`

Arquivo real recomendado no VPS:

    /etc/ai-enterprise-lab/production.env

O arquivo real:

- não deve ficar dentro do repositório;
- não deve ser commitado;
- deve pertencer à conta responsável pelo deployment;
- deve usar permissão `0600`;
- não deve ser exibido integralmente em logs ou troubleshooting.

## Criação no VPS

Criar o diretório com acesso restrito:

    sudo install -d -m 700 /etc/ai-enterprise-lab

Criar inicialmente o arquivo a partir do template:

    sudo install -m 600 infra/.env.prod.example /etc/ai-enterprise-lab/production.env

Depois preencher manualmente os valores reais diretamente no VPS.

Antes de criar novos arquivos sensíveis na sessão, também pode ser usado:

    umask 077

## Secrets

Valores sensíveis atuais:

- `POSTGRES_PASSWORD`
- `REDIS_PASSWORD`
- `N8N_DB_PASSWORD`
- `N8N_ENCRYPTION_KEY`
- `DEEPSEEK_API_KEY`

`DEEPSEEK_API_KEY` somente é necessária quando a integração externa correspondente estiver habilitada.

Não armazenar valores reais:

- no Git;
- em documentação;
- em Dockerfile;
- no build context;
- em screenshots;
- em logs;
- em arquivos compartilhados.

## Uso com Docker Compose

Sempre fornecer explicitamente o arquivo:

    docker compose --env-file /etc/ai-enterprise-lab/production.env -f infra/compose.prod.yaml config --quiet

Para operações de deployment:

    docker compose --env-file /etc/ai-enterprise-lab/production.env -f infra/compose.prod.yaml <command>

Não depender implicitamente do `.env` existente no diretório do projeto.

## Release image tag

`APP_IMAGE_TAG` is required in production.

Use an immutable release identifier, for example:

    APP_IMAGE_TAG=git-a1b2c3d4

Never reuse a tag that has already been deployed. Deterministic rollback
depends on the previous tag still identifying the same application image.

## Validação antes do deployment

Confirmar as permissões:

    stat -c 'mode=%a owner=%U group=%G path=%n' /etc/ai-enterprise-lab/production.env

Resultado esperado:

    mode=600

Validar o Compose sem imprimir a configuração interpolada:

    docker compose --env-file /etc/ai-enterprise-lab/production.env -f infra/compose.prod.yaml config --quiet

Evitar `docker compose config` sem `--quiet` em logs compartilhados, pois a saída normal pode materializar valores interpolados.

## Backup

O arquivo de secrets não deve entrar no backup comum do repositório.

Se for necessário fazer backup das credenciais, usar mecanismo separado, criptografado e com acesso restrito.

## Rotação

Após alteração de password, API key ou outro secret:

1. atualizar o arquivo protegido no host;
2. reiniciar apenas os serviços afetados;
3. validar health e readiness;
4. revogar o secret antigo quando aplicável.

O `N8N_ENCRYPTION_KEY` exige atenção especial. Deve permanecer estável enquanto existirem credenciais do n8n criptografadas com essa chave.
