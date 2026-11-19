---
description: "Task list for Produção e acesso"
---

# Tasks: Produção e acesso

**Input**: Design documents from `/specs/006-producao-e-acesso/`

**Prerequisites**: plan.md, spec.md, research.md, data-model.md, contracts/ (http-api, configuration, messages, estoque-requisito), quickstart.md; constitution v2.3.0

**Tests**: **REQUIRED** (Constitution II). Test tasks come first and a "confirm RED" task proves they fail for the right reason before any implementation. Database tests run on the real Postgres with pgvector; settings are passed as dictionaries (never the process environment); a fake clock drives days and windows; a fake OpenAI-compatible server records the embedding request; no internet.

**Organization**: grouped by user story. Migrations come first because every database test depends on them.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: can run in parallel (different files, no dependency on an incomplete task)
- **[Story]**: US1–US6 from spec.md (none in Setup, Foundational, Polish)
- Every user-facing text lives in `src/pedido/messages.py` and is pt-BR (Constitution I)

---

## Phase 1: Setup

- [X] T001 [P] Write `tests/unit/test_config_producao.py`: `ambiente()`, `host()`, `porta()` (production → `0.0.0.0` and `PORT`, default 10000; otherwise `127.0.0.1` and 8000), `llm_max_tokens()` 4096, `limite_diario_conversa()` 200, `limite_req_por_chave()` 120, `max_llm_concorrentes()` 4, `espera_llm_segundos()` 20, `max_corpo_mensagem_kb()` 64, `embed_send_dimensions()` false, `migrate_on_start()` false; env override and invalid-value fallback; each reads the environment at call time
- [X] T002 Add those readers to `src/pedido/config.py` (run T001) and every new constant of `contracts/messages.md` and the startup/script texts to `src/pedido/messages.py`; run `tests/unit/test_ptbr_strings.py`

---

## Phase 2: Foundational — versioned migrations (blocks every story)

### Tests (write first)

- [X] T003 [P] Write `tests/unit/test_migrate.py` on scratch databases: `aplicar` on an empty database creates the schema, `schema_migrations` and every table of the baseline plus `uso_diario`, recording version, file and checksum; a second `aplicar` changes nothing; migrations run in order and each in its own transaction (a failing migration is rolled back and not recorded, the command raises `ERRO_MIGRACAO_FALHOU`); `status()` lists `aplicada`/`pendente`/`alterada` and changes nothing; an applied file whose checksum changed is `alterada`; `verificar()` raises the pending and the altered messages (the altered one names the file); the baseline adopts a database that already has the 005 schema with orders, models and nicknames intact; the vector size comes from `EMBED_DIMENSIONS` and a different size later is refused with the existing message; every migration file that contains `drop` also contains a `-- BACKUP:` comment
- [X] T004 [P] Extend `tests/unit/test_db.py`: `check_database` in production mode refuses with pending or altered migrations; outside production it refuses unless `migrate_on_start` is true (then it applies); `apply_schema` still works as the wrapper used by fixtures
- [X] T005 **Confirm RED**: run T003–T004; they fail only because `migrate.py` and the migration files do not exist

### Implementation

- [X] T006 [P] Create `src/pedido/migrations/0001_baseline.sql` (the current `schema.sql`, unchanged in behavior, idempotent) and `src/pedido/migrations/0002_uso_diario.sql` (table and RLS)
- [X] T007 Create `src/pedido/migrate.py` (`aplicar`, `status`, `verificar`, the CLI with `--status`) and update `src/pedido/db.py` (`check_database` verifies or applies; `apply_schema` delegates); point `tests/conftest.py` at it; remove `schema.sql` only after the baseline is in place
- [X] T008 **Confirm GREEN**: T003–T004 pass and the whole 005 suite still passes

**Checkpoint**: the schema is versioned; every later table is a migration.

---

## Phase 3: User Story 1 - Only requests with a key can use the API (Priority: P1)

### Tests (write first)

- [X] T009 [P] [US1] Write `tests/unit/test_acesso.py`: `carregar_chaves` parses `name:scopes:key` entries; refuses a malformed entry, a repeated name, an unknown scope and a key under 32 characters with a message that names the entry number and never the key; `Autenticador` accepts `Authorization: Bearer` and `X-API-Key` (`Authorization` wins), compares in constant time (the comparison runs against every key), returns the key name and scopes, and never logs the key (use `caplog`); the per-key rate limiter refuses the 121st request in a minute, does not count refused requests, and does not affect other keys
- [X] T010 [P] [US1] Write `tests/contract/test_api_acesso.py`: with keys configured, every route except `/saude` gives 401 with no key and with a wrong key; 403 for a key without the scope (conversa-only on the model routes, modelo-only on the message and file routes); the right key works as before; errors are `{"erro","mensagem"}` in Portuguese; 429 on the 121st request of a key; the route table test: every route of the app is in `acesso.REGRAS` with the scope its dependency enforces, so a route without a rule fails; no `Access-Control-Allow-Origin` is ever sent; logs hold only the type and the key name
- [X] T011 [P] [US1] Write `tests/contract/test_api_producao.py`: with `ENVIRONMENT=producao`, `/`, `/static/app.js`, `/docs`, `/redoc`, `/openapi.json` answer 404; startup in production without keys is refused with `ERRO_CHAVES_AUSENTES`; outside production without keys the app starts and every route works (a warning is shown); with keys configured outside production the control is on
- [X] T012 [US1] **Confirm RED**: run T009–T011

### Implementation

- [X] T013 [P] [US1] Create `src/pedido/acesso.py` (`Chave`, `carregar_chaves`, `Autenticador`, `exigir(escopo)`, `REGRAS`, the per-key limiter built on `guardrails.RateLimiter` which now takes its limit as a parameter)
- [X] T014 [US1] `src/pedido/web/app.py` and `src/pedido/startup.py`: build the access control from the settings, protect every route, production switches (page, static, docs off), the startup refusals, no CORS
- [X] T015 [US1] **Confirm GREEN**: US1 tests pass; the existing contract tests pass when run with no keys configured

**Checkpoint**: the API is closed to anyone without a key.

---

## Phase 4: User Story 2 - Health check and hosting (Priority: P1)

### Tests (write first)

- [X] T016 [P] [US2] Write `tests/contract/test_api_saude.py`: `/saude` answers 200 `{"status":"ok"}` with no key (also when keys are configured); with the database down (a store whose ping fails) 503 `{"status":"indisponivel"}` and no other field; it answers in under 1 second
- [X] T017 [P] [US2] Write `tests/unit/test_hospedagem.py`: `__main__` builds the server arguments from the environment (host `0.0.0.0` and `PORT` in production, `127.0.0.1:8000` otherwise); the `Dockerfile` exists, runs as a non-root user, copies no `.env`, and its `CMD` is `python -m pedido`; `.dockerignore` excludes `.env*`, `.venv`, `tests`, `specs`, `.specify`; `deploy/render.yaml.example` names `/saude`, the pre-deploy migration command and marks secrets as not synced
- [X] T018 [US2] **Confirm RED**

### Implementation

- [X] T019 [P] [US2] `src/pedido/store.py` (`ping`), `src/pedido/web/app.py` (`GET /saude`), `src/pedido/__main__.py` (host and port)
- [X] T020 [P] [US2] Create `Dockerfile`, `.dockerignore` and `deploy/render.yaml.example`
- [X] T021 [US2] **Confirm GREEN**; build the image once if Docker allows and note the result

---

## Phase 5: User Story 5 - Cost and abuse guardrails (Priority: P1)

### Tests (write first)

- [X] T022 [P] [US5] Write `tests/unit/test_uso_diario.py` on the real database: `registrar_mensagem(conversa, dia, limite)` counts accepted messages, returns nothing once the limit is reached, restarts on a new day, keeps conversations apart, is shared by two `Store` instances; the day is computed in America/Sao_Paulo from an injectable clock
- [X] T023 [P] [US5] Write `tests/unit/test_conversa_custo.py`: the 201st message of a conversation in a day gets `LIMITE_DIARIO`, the language model is not called (stub with no answer left), the pending order is kept, and it works the next day; a database failure in the counter gives `ERRO_BANCO`, not the limit sentence; at most the configured number of language model calls run at once (threads and a slow stub, measure the peak); a message that waits more than the limit gets `OCUPADO` and logs `ocupado`; ok and não are not blocked by the concurrency cap; every log line holds only the type
- [X] T024 [P] [US5] Extend `tests/unit/test_llm.py` and `tests/contract/test_api_mensagem.py`: both adapters pass `LLM_MAX_TOKENS` as `max_tokens` (default 4096); a message body above 64 KB gets 413 `corpo_grande` before the language model is called; the model upload keeps its own limit
- [X] T025 [US5] **Confirm RED**

### Implementation

- [X] T026 [P] [US5] `src/pedido/store.py` (`registrar_mensagem`), `src/pedido/guardrails.py` (`LimiteConcorrencia`), `src/pedido/llm.py` (`max_tokens`)
- [X] T027 [US5] `src/pedido/conversa.py` (daily limit before the language model, concurrency cap around the order call) and `src/pedido/web/app.py` (body limit dependency)
- [X] T028 [US5] **Confirm GREEN**: the whole suite passes

---

## Phase 6: User Story 3 - Startup refuses unsafe states (Priority: P1)

- [X] T029 [P] [US3] Write `tests/contract/test_api_migracoes.py`: the app refuses to start in production with a pending migration (message tells to run the command) and with an altered applied file (message names it); outside production it refuses unless `MIGRATE_ON_START=true`; with the flag it applies and starts; with everything applied it starts
- [X] T030 [US3] **Confirm RED**, then wire `db.check_database` into `create_app` and `startup.check_all`, and **confirm GREEN**

---

## Phase 7: User Story 4 - Hosted embeddings and re-indexing (Priority: P1)

### Tests (write first)

- [X] T031 [P] [US4] Extend `tests/unit/test_embeddings.py`: with `EMBED_SEND_DIMENSIONS=true` the request body (recorded by the fake server) carries `dimensions` equal to `EMBED_DIMENSIONS`; with it off the body carries none; a vector of another size is still discarded; the key never appears in logs or representations
- [X] T032 [P] [US4] Write `tests/unit/test_reindexar.py` and extend `tests/unit/test_script_apelidos.py`: after switching the model, exact-text nicknames still apply and similarity uses only the new model's vectors; `--reindexar` gives every nickname an embedding and the model name of the current model, deletes nothing, prints `REINDEXAR_RESUMO` with the counts; failures of the service are counted and the successes kept; without an embedder it prints `REINDEXAR_SEM_EMBEDDING`
- [X] T033 [US4] **Confirm RED**

### Implementation

- [X] T034 [US4] `src/pedido/embeddings.py` (`dimensions`), `src/pedido/store.py` (`atualizar_embedding`, list for reindexing), `scripts/apelidos.py` (`--reindexar`)
- [X] T035 [US4] **Confirm GREEN**

---

## Phase 8: User Story 6 - Documented contract (Priority: P2)

- [X] T036 [P] [US6] Write `tests/unit/test_docs.py`: `docs/contrato-api.md` lists every route of `acesso.REGRAS` with its scope, every error code and a curl example per route; `docs/producao-render.md` lists every variable of `contracts/configuration.md`, the migration step, `/saude` and a first-deploy checklist; the stock requirement file exists; none of the documents contains a real key
- [X] T037 [US6] **Confirm RED**, then write `docs/contrato-api.md` and `docs/producao-render.md` (Portuguese), copy the stock requirement to `docs/requisito-estoque.md`, and **confirm GREEN**

---

## Phase 9: Polish & Cross-Cutting Concerns

- [X] T038 [P] Update `.env.example` with every new variable (commented, no secrets); update `docs/whatsapp-passo-a-passo.md` (the key and the public route reserved for `/whatsapp`); add an update note to `specs/005-modelo-planilha/spec.md`
- [X] T039 [P] Re-run `tests/unit/test_ptbr_strings.py` with every new text; scan the repository for a real key and for message text or phone numbers in log calls
- [X] T040 Full validation: `uv run pytest`; the quickstart 2–8 on the real app; apply the migrations to a copy of the current development database and compare row counts before and after; record the results in `research.md`
- [X] T041 [P] Final cleanup: no key in any file, `schema.sql` removed in favor of the migrations, `.env` untouched

---

## Dependencies & Execution Order

- **Setup (1)** → **Migrations (2)** → every story. **US1** needs Setup and Migrations. **US2** needs US1 (the health route is the public rule). **US5** needs Migrations (the table) and US1 (the key limiter shares `RateLimiter`). **US3** needs Migrations. **US4** needs Foundational only. **US6** needs US1–US5 (it documents them).
- Within a phase: tests → **Confirm RED** → implementation → **Confirm GREEN**.

## Implementation Strategy

1. **MVP = Migrations + US1 + US2**: a bot that can be hosted and is closed to strangers.
2. Then US5 (cost guards), US3 (startup refusals), US4 (hosted embeddings), US6 (documents), Polish.
3. The real deployment, the stock repository change and the WhatsApp adapter are separate steps.
