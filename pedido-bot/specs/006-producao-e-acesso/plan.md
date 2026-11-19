# Implementation Plan: Produção e acesso

**Branch**: `006-producao-e-acesso` (no git repository; folder name only) | **Date**: 2026-11-18 | **Spec**: [spec.md](spec.md)

**Input**: Feature specification from `/specs/006-producao-e-acesso/spec.md`

## Summary

Make the bot hostable and safe to expose. Five additions, none visible in the customer's reply:
(1) **access control**: keys (name, scopes, secret) read from `API_KEYS`, a FastAPI dependency per route that
returns 401 or 403, a per-key rate limit, a test listing every route with its rule; in production the page and
the docs are off and the start is refused without keys. (2) **health check and hosting**: public `GET /saude`,
host and port from the environment, a `Dockerfile`, `.dockerignore` and a Render example. (3) **versioned
migrations**: `src/pedido/migrations/0001_baseline.sql` (today's schema, idempotent) and `0002_uso_diario.sql`,
applied by `python -m pedido.migrate` with version and checksum in `schema_migrations`; the application
verifies instead of applying (unless `MIGRATE_ON_START=true` outside production). (4) **hosted embeddings**:
`dimensions` sent when asked, a `--reindexar` option in the nicknames script. (5) **cost guardrails**: a daily
limit per conversation stored in `uso_diario`, `max_tokens` on every language model call, a concurrency cap with
a short wait, a 64 KB message body limit. Plus the documents: API contract, hosting guide, requirement for the
stock repository. See [research.md](research.md).

## Technical Context

**Language/Version**: Python 3.11 (`uv`), unchanged. **Dependencies**: no new package (`hmac`, `hashlib`,
`zoneinfo`, `threading` are standard).

**Storage**: Postgres 16 + pgvector; new tables `schema_migrations` and `uso_diario`; the baseline keeps every
existing table.

**Testing**: pytest on real Postgres; the app is built with explicit settings (environment dictionaries, never
the process environment) so tests of production behavior do not depend on the machine; fake OpenAI-compatible
server for the embedding request; a fake clock for the day and for the windows; no network.

**Target Platform**: a Linux container on a hosting platform (Render as the example) with a managed Postgres
(Supabase as the example); local macOS for development.

**Performance Goals**: authentication adds well under 1 ms per request; the health check answers in under 1 s;
the daily counter is one upsert per message.

**Constraints**: replies for normal orders unchanged; keys and message text never in logs; one shared counter
(database) only for the daily limit; every other limit is per instance in memory.

## Constitution Check

*GATE: passed before Phase 0; re-checked after Phase 1.* Constitution **v2.3.0**.

| Principle / constraint | Gate | Status |
|---|---|---|
| I. pt-BR everywhere | every new reply, API error, startup message and script output is a constant of `messages.py`; scanner test covers them | PASS |
| II. Test-First | tests first for access, health, migrations, embeddings request, each guardrail; real Postgres; fake clock and fake server | PASS (tasks ordering) |
| III. The Customer Confirms | daily-limit and busy sentences are one neutral sentence, pending order kept | PASS |
| IV. Closest Match | untouched; exact-text nicknames survive an embedding model switch | PASS |
| V. Deterministic Core | access, limits and migrations are plain Python; embeddings only look up | PASS |
| VI. Orders Are Persisted | versioned migrations with checksum; refuse to start when pending or altered; baseline = today's schema | PASS |
| VII. Scope | no WhatsApp adapter, accounts, billing, stock login or real deploy | PASS |
| VIII. Guardrails | daily limit, max output, per-key rate, body size, concurrency cap, type-only logs | PASS |
| IX. Controlled Access | keys from the environment, constant-time compare, 401/403, scopes, only `/saude` public, page and docs off in production, bind | PASS |
| Tech: hosting, migrations, hosted embeddings | see research D2 to D8 | PASS |

Post-design re-check: **PASS**, no violations.

## Project Structure

### Documentation (this feature)

```text
specs/006-producao-e-acesso/
├── plan.md  research.md  data-model.md  quickstart.md
├── contracts/ (http-api.md, configuration.md, messages.md, estoque-requisito.md)
├── checklists/requirements.md
└── tasks.md            # /speckit-tasks output (NOT created here)
```

### Source Code (repository root)

```text
src/pedido/
├── config.py         # ambiente(), host(), porta(), the new limits (all from the environment)
├── messages.py       # new errors, replies, startup and script texts
├── acesso.py         # NEW: Chave, carregar_chaves(env), Autenticador, REGRAS of routes, per-key rate limit
├── guardrails.py     # RateLimiter takes its limit; LimiteConcorrencia; registrar(tipo) reused
├── migrate.py        # NEW: aplicar(), status(), verificar(); the CLI `python -m pedido.migrate`
├── migrations/       # NEW: 0001_baseline.sql, 0002_uso_diario.sql
├── db.py             # check_database verifies migrations (or applies with MIGRATE_ON_START); apply_schema delegates
├── store.py          # registrar_mensagem(conversa, dia, limite), atualizar_embedding, health ping
├── embeddings.py     # `dimensions` when EMBED_SEND_DIMENSIONS=true
├── llm.py            # max_tokens on both adapters
├── conversa.py       # daily limit and concurrency cap before the language model
├── startup.py        # validates API_KEYS, ENVIRONMENT, PORT, migrations
├── __main__.py       # host and port from the environment
└── web/app.py        # dependencies, /saude, page and docs off in production, body limit, 429/413
scripts/apelidos.py   # + --reindexar
Dockerfile  .dockerignore  deploy/render.yaml.example
docs/contrato-api.md  docs/producao-render.md
tests/                # new unit and contract tests; the route table test
```

**Structure Decision**: one new module for access (`acesso.py`) and one for migrations (`migrate.py`); the rest
extends existing modules. The schema file moves into numbered migrations; `db.apply_schema` stays as a thin
wrapper (used by tests and scratch databases) that calls the migration runner.

## Complexity Tracking

No constitution violations to justify.
