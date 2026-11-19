# Research: Produção e acesso

No `NEEDS CLARIFICATION` remains.

## D1 — Keys (`acesso.py`)

`API_KEYS="estoque:conversa+modelo:KEY1,whatsapp:conversa:KEY2"`. Parsed into `Chave(nome, escopos, segredo)`.
Startup refuses (message names the entry NUMBER, never the key) when: an entry is malformed (needs 3 parts),
a name repeats, a scope is unknown, or a key is shorter than 32 characters. The request key comes from
`Authorization: Bearer` (wins) or `X-API-Key`. Lookup compares the sent key against EVERY stored key with
`hmac.compare_digest` (no early exit) and keeps the match. Nothing is logged but the type and, when known,
the key name.

## D2 — Route rules and the table test

A dependency factory `exigir(escopo)` gives 401 (`chave_ausente`, `chave_invalida`), 403 (`sem_permissao`) and
429 (per-key limiter, `muitas_requisicoes`). `acesso.REGRAS` maps `(method, path)` to the scope or `None`
(public): `POST /api/mensagem` and `GET /api/pedidos/{pedido_id}/planilha` → `conversa`; `GET|POST /api/modelo`
and `GET /api/modelo/info` → `modelo`; `GET /saude` → public. A test walks `app.routes` and fails for any
route missing from the table or whose dependency disagrees. When no key is configured outside production, the
dependency lets everything through and the start prints a warning.

## D3 — Production switches

`config.ambiente()` reads `ENVIRONMENT` (`producao` or anything else). In production: `FastAPI(docs_url=None,
redoc_url=None, openapi_url=None)`, the home page and `/static` are not registered (404), startup refuses
without keys. Outside production the page and docs stay (they are useful and protected by keys when set).
No CORS middleware is ever added. `config.host()`/`porta()`: production → `0.0.0.0` and `PORT` (default
10000); else `127.0.0.1:8000`.

## D4 — Health check

`GET /saude` runs `select 1` through the store; 200 `{"status":"ok"}` or 503 `{"status":"indisponivel"}`; no
other field; exceptions are swallowed (logged by type).

## D5 — Migrations (`migrate.py`)

Files `src/pedido/migrations/NNNN_name.sql`, applied in name order. Table `pedido.schema_migrations(versao
text primary key, arquivo text, checksum text, aplicada_em timestamptz)`; the schema and the table are created
by the runner itself before reading it. Checksum = SHA-256 of the raw file (the `__DIMENSIONS__` placeholder
is replaced only when executing). Each file runs in its own transaction with its record. `status()` returns
each file as `aplicada`, `pendente` or `alterada`; `verificar()` raises a Portuguese `StartupError` for
pending or altered. `0001_baseline.sql` is today's `schema.sql` (all `if not exists`, so it adopts an existing
database; the guarded legacy cleanup and the vector extension stay in it). `0002_uso_diario.sql` adds
`pedido.uso_diario(conversa text, dia date, mensagens integer not null default 0, primary key (conversa, dia))`
with RLS. `db.check_database`: outside production and without `MIGRATE_ON_START=true` it also refuses when
pending; with the flag it applies. The vector-size check (`ERRO_DIMENSAO_DIFERENTE`) stays.

## D6 — Daily limit

`store.registrar_mensagem(conversa, dia, limite)`: one statement `insert ... on conflict (conversa, dia) do
update set mensagens = mensagens + 1 where uso_diario.mensagens < limite returning mensagens`; no row back =
limit reached. `Conversa` calls it first (before reading the reply type, after the per-conversation window
limiter) with `dia` = today in `America/Sao_Paulo` (injectable clock). A refused message gets `LIMITE_DIARIO`
and never reaches the language model. A database failure there is treated like any database failure
(`ERRO_BANCO`), not as "limit reached".

## D7 — Language model limits

`LLM_MAX_TOKENS` (default 4096) passed as `max_tokens` to both adapters. `guardrails.LimiteConcorrencia(n,
espera)` wraps only the language model call of an order (a `BoundedSemaphore` and `acquire(timeout)`); a
timeout gives `OCUPADO` and logs `ocupado`. The message body limit (64 KB) is a dependency of
`POST /api/mensagem` that reads the body once and answers 413 `corpo_grande` before parsing it.

## D8 — Hosted embeddings

`OpenAIEmbeddings(dimensions=N)` only when `EMBED_SEND_DIMENSIONS=true` (the fake server records the body, so a
test sees `dimensions`). `scripts/apelidos.py --reindexar` embeds every nickname's text with the current model
and updates `embedding` and `modelo` (never deleting), printing `Reindexados: X. Falhas: Y.`; without an
embedder it refuses in Portuguese.

## D9 — Packaging

`Dockerfile`: `python:3.11-slim`, `uv sync --frozen --no-dev`, a non-root user, `CMD ["python", "-m", "pedido"]`;
no `.env`, no secrets; `.dockerignore` excludes `.env*`, `.venv`, `tests`, `specs`, `.specify`, `docs`.
`deploy/render.yaml.example`: a web service with the health check `/saude`, `preDeployCommand: python -m
pedido.migrate`, and the variable names with `sync: false` for secrets. Example only; no deploy here.

## D10 — Documents

`docs/contrato-api.md` (keys, scopes, errors, curl examples) and `docs/producao-render.md` (variable table,
migration step, health check, first-deploy checklist); `contracts/estoque-requisito.md` states what the stock
repository must do (an environment variable for the key, the `Authorization` header from its backend only, the
scopes `conversa` and `modelo`, the private bot address).

## D11 — What does not change

Replies for normal orders, the engine, the memory, the model management, the states of orders. The chat page
keeps working locally.

## Medição final (2026-11-18)

- 640+ testes verdes (Postgres com pgvector real; relógio e servidor falsos).
- **Adoção do banco de desenvolvimento**: numa cópia do banco, antes e depois de `python -m pedido.migrate`:
  pedidos 20 → 20, modelos 5 → 5, apelidos 2 → 2, catálogo 169 → 169; a tabela `uso_diario` passou a existir e a
  segunda execução respondeu "Nenhuma migração pendente".
- **Container** (imagem construída de verdade, 752 MB): roda como usuário 10001 (não-root); sem migração aplicada
  recusa iniciar e manda rodar `python -m pedido.migrate`; sem `API_KEYS` em produção recusa iniciar; depois de
  migrar, `GET /saude` responde 200, `/api/modelo/info` responde 401 sem chave e 200 com chave, `/docs` e a
  página respondem 404.
- A primeira construção da imagem falhou por tempo esgotado ao baixar a imagem base (rede), sem relação com o
  Dockerfile; baixando a base antes, a construção levou cerca de 20 s.
