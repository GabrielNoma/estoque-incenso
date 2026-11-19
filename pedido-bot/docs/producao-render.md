# Publicando o bot no Render (guia de produção)

O bot roda como um serviço web separado (Python, em container). O banco é um Postgres com a extensão
`vector` (por exemplo, o Supabase). Os nomes das telas do Render e do Supabase mudam: confira na
documentação deles. Um exemplo de configuração está em `deploy/render.yaml.example`.

## Variáveis de ambiente do serviço do bot

**Secretas** (no Render: variável de ambiente do serviço; nunca no repositório):

| Variável | Para quê |
|---|---|
| `ANTHROPIC_API_KEY` | chave da Anthropic (modelo que lê o pedido) |
| `DATABASE_URL` | conexão do Postgres (Supabase) |
| `API_KEYS` | chaves de quem consome a API: `nome:escopos:chave,...` |
| `EMBED_API_KEY` | chave do serviço de embeddings (se usar a memória) |

**Não secretas:**

| Variável | Valor / padrão |
|---|---|
| `ENVIRONMENT` | `producao` |
| `PORT` | o Render define sozinho; não declare |
| `LLM_PROVIDER` | `anthropic` |
| `LLM_MODEL` | `claude-haiku-5-5` |
| `LLM_MAX_TOKENS` | 4096 |
| `LLM_TIMEOUT_SECONDS` | 180 |
| `EMBED_BASE_URL`, `EMBED_MODEL` | serviço de embeddings (opcional; sem eles a memória fica desligada) |
| `EMBED_DIMENSIONS` | 1024 (tamanho do vetor da tabela de apelidos) |
| `EMBED_SEND_DIMENSIONS` | `true` para pedir esse tamanho ao serviço |
| `EMBED_SIMILARITY` | 0.92 |
| `LIMITE_DIARIO_CONVERSA` | 200 mensagens por conversa por dia |
| `LIMITE_MSG_POR_MINUTO` | 20 mensagens por conversa por minuto |
| `LIMITE_REQ_POR_CHAVE` | 120 requisições por chave por minuto |
| `MAX_LLM_CONCORRENTES` | 4 chamadas ao modelo ao mesmo tempo |
| `ESPERA_LLM_SEGUNDOS` | 20 s de espera por uma vaga |
| `MAX_CORPO_MENSAGEM_KB` | 64 |
| `MAX_MODELO_MB` | 5 |
| `MIGRATE_ON_START` | não use em produção (só para uso local) |

## Migrações do banco

O aplicativo **não** altera o banco ao iniciar: ele recusa iniciar se houver migração pendente ou arquivo
alterado. Antes de cada versão nova, rode:

```bash
python -m pedido.migrate            # aplica as pendentes, em ordem
python -m pedido.migrate --status   # só mostra: aplicada, pendente ou alterada
```

Use a conexão do Supabase que aceita DDL (a conexão direta ou o pooler de modo sessão); o pooler de modo
transação serve para o aplicativo. No Supabase, habilite a extensão `vector` antes (Database → Extensions).

## Health check

Configure o health check do Render para `GET /saude` (responde `200 {"status":"ok"}` quando o aplicativo e o
banco respondem, `503` caso contrário).

## Checklist do primeiro deploy

- [ ] Projeto do Supabase com a extensão `vector` habilitada e a string de conexão copiada
- [ ] Repositório no GitHub com a pasta `pedido-bot/` e sem nenhum `.env` versionado
- [ ] Serviço web criado no Render apontando para `pedido-bot` (Docker), health check em `/saude`
- [ ] Variáveis secretas preenchidas no painel do Render (`ANTHROPIC_API_KEY`, `DATABASE_URL`, `API_KEYS`)
- [ ] Chaves de `API_KEYS` geradas com `secrets.token_urlsafe(32)`, uma por consumidor
- [ ] Migrações aplicadas com `python -m pedido.migrate` antes do primeiro início
- [ ] `GET /saude` responde 200 e as rotas respondem 401 sem chave
- [ ] No serviço do estoque: `PEDIDO_BOT_URL` e `PEDIDO_BOT_API_KEY` configurados
- [ ] Teste de ponta a ponta: pedido, `ok` e download da planilha pela tela do estoque
- [ ] Deploy hook do serviço guardado como secret do GitHub (`RENDER_DEPLOY_HOOK_URL_BOT`)

## Cuidados

- O plano gratuito do Render faz o serviço dormir sem uso; a primeira mensagem depois disso demora. Para o
  WhatsApp, prefira um plano que fique sempre ligado.
- Revogue qualquer chave que tenha sido colada em chat ou em arquivo versionado e gere outra.
- Os logs registram só o tipo de cada bloqueio (e o nome da chave), nunca o texto, o telefone ou a chave.

## CI/CD (GitHub Actions)

O arquivo `.github/workflows/deploy.yml`, na raiz do repositório, tem dois trabalhos que só rodam quando a pasta
deles muda: `estoque` (testes do backend, build do Angular, deploy do estoque) e `bot` (testes do bot com
Postgres + pgvector, construção da imagem do container, migrações e deploy do bot). Em pull requests só
testa; o deploy acontece apenas em push no `main`, depois dos testes.

| Secret do GitHub (Settings → Secrets → Actions) | Para quê |
|---|---|
| `RENDER_DEPLOY_HOOK_URL` | deploy hook do serviço do estoque (já existe) |
| `RENDER_DEPLOY_HOOK_URL_BOT` | deploy hook do serviço do bot (copie do painel do serviço no Render) |
| `BOT_DATABASE_URL_MIGRACAO` | conexão do Supabase que aceita DDL, usada só para aplicar as migrações antes do deploy |

As chaves do modelo (`ANTHROPIC_API_KEY`), `API_KEYS` e a `DATABASE_URL` do aplicativo ficam **só no Render**,
não no GitHub. Se `BOT_DATABASE_URL_MIGRACAO` não existir, o CI avisa e não migra: rode
`python -m pedido.migrate` por conta própria antes do deploy. Escreva as migrações de forma compatível com a
versão anterior do código (só acrescentar), porque a versão antiga ainda atende durante o deploy.
