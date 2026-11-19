---
description: "Task list for Banco único, serviços de IA configuráveis e memória de pedidos"
---

# Tasks: Banco único, serviços de IA configuráveis e memória de pedidos

**Input**: Design documents from `/specs/002-rag-memory-providers/`

**Prerequisites**: plan.md, spec.md, research.md, data-model.md, contracts/ (configuration, http-api-changes, reprocess-cli), quickstart.md; constitution v1.1.0

**Tests**: **REQUIRED** (Constitution II). Test tasks come first in every phase, a "confirm RED" task
proves they fail for the right reason, and only then does implementation start. Database tests run
against the **real Postgres + pgvector in Docker**; the LLM and embedder are replaced by stubs, a
deterministic `FakeEmbedder` and a fake OpenAI-compatible server, so no test needs the internet.

**Organization**: grouped by user story. US1 and US2 are P1, US3 and US4 are P2, US5 is P3. Feature 001
must keep passing: its tests are **migrated**, never deleted.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: can run in parallel (different files, no dependency on an incomplete task)
- **[Story]**: US1–US5 from spec.md (none in Setup, Foundational, Polish)
- All user-facing text is pt-BR and lives in `src/pedido/messages.py` (Constitution I)

## Path Conventions

Single project at `/Users/gabrielmnoma/Coding/tests/project-R`: `src/pedido/`, `tests/`, `scripts/`,
`assets/`; new root files `docker-compose.yml` and `.env.example` (plan.md).

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: dependencies, local Postgres, configuration template

- [X] T001 Add `psycopg[binary]`, `pgvector` and `langchain-openai` to `pyproject.toml` and run `uv sync` (versions resolved and locked by `uv`; the stdlib `sqlite3` is no longer used by the project)
- [X] T002 [P] Create `docker-compose.yml` with a `db` service (`pgvector/pgvector:pg16`, port `5433:5432`, user/password/database `pedido`, a named volume, a `pg_isready` healthcheck)
- [X] T003 [P] Create `.env.example` listing every variable of `contracts/configuration.md` with safe local defaults (`DATABASE_URL=postgresql://pedido:pedido@localhost:5433/pedido`) and **no secrets**
- [X] T004 Make the database available: start Docker Desktop if its daemon is not running (`open -a Docker`, wait until `docker info` answers), run `docker compose up -d db`, and verify with a one-off `uv run python` that `select version()` and `create extension if not exists vector` work on `localhost:5433`

**Checkpoint**: a reachable pgvector Postgres on `localhost:5433` and the new dependencies installed.

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: database module and schema, configuration, messages, and the test doubles every story uses.
**No user story starts until this phase is green.**

### Tests first (write all, then confirm they fail)

- [X] T005 [P] Write `tests/unit/test_fakes.py` for the test doubles: `FakeEmbedder` is deterministic, returns L2-normalized vectors of the configured size, cosine similarity grows with word overlap, accepts explicit per-text overrides, records each call with its batch, and can be set to fail or time out; the fake OpenAI-compatible server (random local port) records requests to `/v1/chat/completions` and `/v1/embeddings` (path, bearer key, JSON body) and can be set to answer with an error
- [X] T006 [P] Write `tests/unit/test_db.py`: `apply_schema` creates schema `pedido` with all six tables and the vector extension and is **idempotent** (run twice); row-level security is enabled on every table; `check_database` accepts a good database; `current_dimension` reads the vector size of `memoria_linhas`; the HNSW indexes exist; the connection helper registers the vector type and uses no prepared statements
- [X] T007 [P] Extend `tests/conftest.py` with the real-database fixtures: a session fixture that creates (if needed) the test database `pedido_test` through the admin connection on `localhost:5433`, applies `schema.sql`, and **fails with a clear message** (`docker compose up -d db`) if Postgres is unreachable instead of skipping; a per-test fixture that runs `TRUNCATE ... RESTART IDENTITY CASCADE` on every table; a `database_url` fixture; an `embedder` fixture returning a `FakeEmbedder`; an `openai_server` fixture for the fake server (imports stay lazy so unit tests of pure modules still run without Postgres)
- [X] T008 **Confirm RED**: run `uv run pytest tests/unit/test_fakes.py tests/unit/test_db.py` and confirm every test fails only because `tests/fakes.py`, `pedido.db`, `schema.sql` and the new config entries do not exist yet (not because of a typo in the tests)

### Implementation

- [X] T009 [P] Implement `tests/fakes.py` (`FakeEmbedder`, the fake OpenAI-compatible server as a small FastAPI app served in a background thread on a random port) to make `tests/unit/test_fakes.py` pass
- [X] T010 [P] Extend `src/pedido/config.py`: `DATABASE_URL`, `LLM_PROVIDER`, `LLM_MODEL`, `LLM_BASE_URL`, `LLM_STRUCTURED_METHOD`, `EMBED_*` settings read from the environment (keys only through accessor functions, never stored), the memory constants (`MEMORY_NEIGHBORS=5`, `MEMORY_MIN_SIMILARITY=0.82`, `MEMORY_PRESELECT_SIMILARITY=0.90`, `MESSAGE_EXAMPLES=3`, `MESSAGE_MIN_SIMILARITY=0.75`, `MESSAGE_EMBED_MAX_CHARS=2000`); the SQLite path (`DB_PATH`) stays until T022 removes it, because the old `Store` still uses it until US1
- [X] T011 [P] Extend `src/pedido/messages.py` with every new pt-BR string: the six startup messages of `contracts/configuration.md`, `ERRO_BANCO` and its code `erro_banco`, the memory states ("Memorizado", "Memória pendente"), the reason label "parecido com um pedido anterior", and the reprocess output lines (`tests/unit/test_ptbr_strings.py` already scans this module)
- [X] T012 Create `src/pedido/schema.sql` (idempotent DDL of `data-model.md`, rendered with `{dim}`) and `src/pedido/db.py`: `StartupError` (carries the pt-BR message), `connect(url)` (psycopg 3, `prepare_threshold=None`, `register_vector`), `apply_schema(url, dim)`, `current_dimension(url)`, `check_database(url, dim)` (5 s connect timeout, extension and dimension checks, raising `StartupError` with the right message), to make `tests/unit/test_db.py` pass
- [X] T013 **Confirm GREEN**: `uv run pytest tests/unit/test_fakes.py tests/unit/test_db.py tests/unit/test_ptbr_strings.py` all pass

**Checkpoint**: schema applies idempotently on the real database; fakes and fixtures are ready.

---

## Phase 3: User Story 1 - Everything saved in one durable database (Priority: P1) 🎯

**Goal**: the tool behaves exactly as in 001 but on Postgres only; it refuses to start in Portuguese
without a reachable database; no application data in local files.

**Independent Test**: approve an order, restart, and see history, aliases and download intact; start
without a database and get the Portuguese refusal.

### Tests for User Story 1 (write first)

- [X] T014 [P] [US1] Migrate `tests/unit/test_store.py` to the Postgres `Store(database_url)` keeping every 001 assertion (tables, alias upsert latest-wins, suggestion beside final answer, approved run immutable, omitted lines kept with null finals, user-added line) and add: a **new `Store` instance sees data written by another** (survives restart); `memoria_estado` is `nao_aplicavel` for a new run; `approve_run` is **atomic** (a failure while storing the lines leaves the run `proposto` with no finals)
- [X] T015 [P] [US1] Write `tests/unit/test_startup.py`: `DATABASE_URL` missing → `StartupError` with the pt-BR message; unreachable address (closed port) → the connection message; dimension mismatch → the dimension message; partial embeddings config → "falta …" listing the variables; invalid `LLM_PROVIDER` → its message; and `python -m pedido` run as a subprocess without `DATABASE_URL` prints the Portuguese message and exits with code 1
- [X] T016 [P] [US1] Migrate the 001 contract and integration tests and `tests/conftest.py` fixtures to `create_app(database_url=..., chat_model=..., embedder=None)` and the new `store` fixture, keeping every assertion (`tests/contract/test_api_*.py`, `tests/integration/test_proposal_chain.py`, `tests/unit/test_alias_learning.py`, `tests/unit/test_export.py` where they touch the store)
- [X] T017 [P] [US1] Write `tests/contract/test_api_banco.py`: when a database operation fails while the app runs (simulated by making the connection raise `OperationalError`) the API answers **503 `erro_banco`** with the pt-BR message; an approval whose write fails halfway leaves the order `proposto` and nothing partly saved; after the failure stops, the same request succeeds (recovery); no application data is written to local files other than the downloaded spreadsheet
- [X] T018 [US1] **Confirm RED**: run the migrated and new US1 tests; confirm they fail only because the Postgres `Store`, the new `create_app` signature and `python -m pedido` do not exist yet

### Implementation for User Story 1

- [X] T019 [US1] Rewrite `src/pedido/store.py` for Postgres with the same public API as 001 (`save_catalog`, `get_alias`, `upsert_alias`, `create_run`, `add_line`, `get_run`, `list_runs`, `approve_run`, `table_names`), a connection per operation through `pedido.db.connect`, `RETURNING` ids, native `boolean`/`jsonb`/`timestamptz` converted to the same Python shapes (ISO strings), `memoria_estado` on runs, and `approve_run` in a single transaction
- [X] T020 [US1] Update `src/pedido/web/app.py`: `create_app(database_url=None, chat_model=None, embedder=None, template_path=None)` reads `DATABASE_URL` when not given, calls `check_database`/`apply_schema` and raises `StartupError`; add the `OperationalError` handler returning 503 `erro_banco` (and register the code in `messages.ERROS`); `pedido.web.app:app` keeps building lazily
- [X] T021 [US1] Create `src/pedido/__main__.py`: `python -m pedido` validates the configuration, prints the Portuguese `StartupError` message and exits with code 1, or starts Uvicorn on `127.0.0.1:8000`
- [X] T022 [US1] Remove every SQLite remnant: `grep` for `sqlite3`, `data/pedido.db`, `DB_PATH` in `src/`, `tests/`, `scripts/` and docs, delete the empty `data/` directory, and update `scripts/run_regression_real.py` and the 001 quickstart note that referenced the SQLite file
- [X] T023 [US1] **Confirm GREEN**: the whole migrated 001 suite plus the new US1 tests pass on Postgres; run quickstart scenarios 1–3 (no `DATABASE_URL`, stopped Postgres, restart keeps the history)

**Checkpoint**: single Postgres database, same behavior as 001, Portuguese refusal at startup.

---

## Phase 4: User Story 2 - Choose the AI services by configuration (Priority: P1) 🎯

**Goal**: the language model (Claude or any OpenAI-compatible service) and the embeddings service are
chosen by environment variables only; failures keep the user's text; keys never leak.

**Independent Test**: run the same proposal through each provider via the fake server and via
Claude's adapter; remove a key and see the Portuguese fallback; scan responses for the key.

### Tests for User Story 2 (write first)

- [X] T024 [P] [US2] Write `tests/unit/test_llm.py`: `build_chat_model` for `anthropic` builds the Claude adapter lazily (no key needed to start); for `openai_compatible` it sends a request to the fake server's `/v1/chat/completions` with the bearer key, the model name and a JSON-schema response format, and parses the structured answer into the Pydantic schema; `LLM_STRUCTURED_METHOD=function_calling` switches the request to tool calling; a missing address, model or key raises a clear error on first use (never at startup); an invalid provider is rejected; `repr`/`str` of the adapters never contain the key
- [X] T025 [P] [US2] Write `tests/unit/test_embeddings.py`: `OpenAICompatibleEmbedder` posts to `/v1/embeddings` with `input` as a **list of strings** (not token ids), the bearer key, the model and `dimensions`, one request per batch, and returns the vectors in order; `SafeEmbedder` returns `None` (never raises) on HTTP errors, connection refused, timeout and when unconfigured; logs contain the error class but never the key or the text; `build_embedder` returns `None` when nothing is configured and raises the "configuração incompleta" error for a partial configuration
- [X] T026 [P] [US2] Write `tests/contract/test_api_provedores.py`: with the OpenAI-compatible adapter pointed at the fake server, `POST /api/pedidos` returns a normal proposal; with no key or address the answer is the 001 **502 `analise_indisponivel`** with the message kept and an empty table; the fake key string never appears in any response body, history entry or database row
- [X] T027 [US2] **Confirm RED**: run the three US2 test files; confirm they fail only because `pedido.llm` and `pedido.embeddings` do not exist yet

### Implementation for User Story 2

- [X] T028 [P] [US2] Implement `src/pedido/llm.py`: `build_chat_model(env=os.environ)` returning a lazy chat object for `anthropic` (as the old `_LazyChat`) or `openai_compatible` (`ChatOpenAI(base_url, api_key, model, temperature=0)` with `with_structured_output(method=LLM_STRUCTURED_METHOD)`), plus clear configuration errors raised on first use
- [X] T029 [P] [US2] Implement `src/pedido/embeddings.py`: `Embedder` protocol (`embed_batch(texts) -> list[list[float]]`), `OpenAICompatibleEmbedder` (`OpenAIEmbeddings(check_embedding_ctx_length=False, timeout=EMBED_TIMEOUT_SECONDS, max_retries=1)`), `SafeEmbedder` (any failure → `None`, logs only the error class), `build_embedder(env)`
- [X] T030 [US2] Wire both into `create_app` and the lazy `pedido.web.app:app` (replace `_LazyChat`), and extend `scripts/run_regression_real.py` with `--provider`, `--model` and `--base-url` so the regression messages can be run through either provider
- [X] T031 [US2] **Confirm GREEN**: US2 tests pass; quickstart scenario 9 is run against the fake server here (with real services it is repeated in T061)

**Checkpoint**: P1 stories done: Postgres only, providers by configuration. Feature 001 intact.

---

## Phase 5: User Story 3 - Remember the orders the user confirms (Priority: P2)

**Goal**: at approval, remember the message with its final lines and each line's text with its confirmed
product; never block an approval; complete pending memory with a reprocess command; show the memory
state in the history.

**Independent Test**: approve with the embedder up (history "Memorizado") and down (approval succeeds,
"Memória pendente"), then reprocess.

### Tests for User Story 3 (write first)

- [X] T032 [P] [US3] Write `tests/unit/test_memory_write.py`: `write_for_run` stores rows only for **final** lines with non-empty text and a product (auto-accepted approved lines included; removed lines, unconfirmed suggestions and lines without text never); re-confirming the same wording and product upserts and refreshes `confirmado_em`; the message and all line texts go in **one** embedding batch; embedder returning `None` → rows with `embedding NULL` and `runs.memoria_estado = 'pendente'`, otherwise `completa`; `modelo_embedding` is recorded; the stored message is complete while the vector uses at most 2,000 characters; one memory per run
- [X] T033 [P] [US3] Write `tests/unit/test_reprocess.py`: pending rows get vectors and runs become `completa`; running twice changes nothing and creates no duplicates; an embedder that fails after the first batch leaves the rest pending and a second run finishes them; rows made with another `modelo_embedding` are recomputed and a colliding older duplicate is dropped; `--dry-run` only reports counts; exit codes 0, 1 (configuration/database) and 2 (still pending); output is pt-BR and never prints keys or message text
- [X] T034 [P] [US3] Write `tests/contract/test_api_memoria.py`: **an approval succeeds with `200` when the embedder fails or times out** and the order's history shows `memoria: "pendente"` / "Memória pendente"; with the embedder up it shows `"memorizado"` / "Memorizado"; the approve response carries the same fields; a run that is only proposed has no memory state; no response contains a key
- [X] T035 [US3] **Confirm RED**: run the three US3 test files; confirm they fail only because the memory write, `pedido.reprocess` and the history field do not exist

### Implementation for User Story 3

- [X] T036 [US3] Add the memory tables' operations to `src/pedido/store.py` (insert/upsert memory lines and messages, set `memoria_estado`, select pending rows, update vectors/models, drop colliding duplicates) and create `src/pedido/memory.py` with `write_for_run(store, embedder, run, finals, model)` following research D6 (a **separate transaction after** the approval commit; it never raises)
- [X] T037 [US3] Add the write step to `src/pedido/chains.py` (`build_write_memory`, run after `save_corrections` in the approval route) and expose `memoria`/`memoria_rotulo` in the approve response, the history list and the detail in `src/pedido/web/app.py`
- [X] T038 [US3] Implement `src/pedido/reprocess.py` (`python -m pedido.reprocess [--batch N] [--dry-run]`, behavior and exit codes of `contracts/reprocess-cli.md`, pt-BR output from `messages.py`)
- [X] T039 [US3] Show "Memorizado" / "Memória pendente" in the history list and detail, and a note after approval when the memory is pending, in `src/pedido/web/templates/index.html` and `src/pedido/web/static/app.js`
- [X] T040 [US3] **Confirm GREEN**: US3 tests pass; quickstart scenarios 4–6 run with the fake embedder server

**Checkpoint**: confirmed data is remembered; an outage never costs an approval.

---

## Phase 6: User Story 4 - Better suggestions while matching (Priority: P2)

**Goal**: flagged lines get candidates reordered and a pre-selection from remembered lines, with the
Portuguese reason, never auto-accepted, never confusing look-alike products.

**Independent Test**: seed the memory with confirmed lines, paste similar wordings, and check order,
pre-selection, reason, blocked approval and the look-alike cases.

### Tests for User Story 4 (write first)

- [X] T041 [P] [US4] Author `tests/fixtures/memoria/linhas_confirmadas.json`: confirmed lines (written text → product) to fill the memory, plus the query lines and expectations for SC-004 (the flagged regression lines that resemble a confirmed line, including "sete linhas" → "7 Linhas") and the look-alike cases (remembered "abre caminho" vs query "abre caminho da felicidade"; remembered "abre c da felicidade" vs "abre caminho")
- [X] T042 [P] [US4] Write `tests/unit/test_memory_guard.py` for the pure functions of research D5: `token_compatible` (same token count and each sorted pair ≥ 80), `may_preselect` (similarity ≥ 0.90 **and** first word unique **or** token-compatible), `merge_candidates` (best of fuzzy score and similarity×100, at most 3, most recent first on equal products); "abre caminho" vs "abre caminho da felicidade" is **not** pre-selectable, "abre camiho" vs "abre caminho" is
- [X] T043 [P] [US4] Write `tests/unit/test_memory_neighbors.py` for the store query: cosine order, same `modelo_embedding` only, `embedding NULL` excluded, similarity threshold, deduplicated by product with the best similarity, ties by most recent `confirmado_em`, at most `MEMORY_NEIGHBORS`
- [X] T044 [P] [US4] Write `tests/unit/test_match_memory.py`: for lines needing review, remembered products reorder the candidates and may pre-select with `motivo="memoria"` and `precisa_revisao=True` (**never auto-accepted**); exact, alias and safe-fuzzy lines never consult memory; a lookup returning `None` or raising gives exactly the 001 result; the same wording confirmed for two products offers both, most recent first; look-alike guard cases from T041
- [X] T045 [P] [US4] Write `tests/contract/test_api_ajuda_memoria.py` and `tests/integration/test_memory_flow.py`: approve a corrected line, then a similar wording returns `motivo: "memoria"`, `motivo_rotulo: "parecido com um pedido anterior"`, candidates with `origem`, and `aprovar` still returns **409** until `confirmado` is sent; the look-alike scenario never pre-selects "Abre Caminho" for "abre caminho da felicidade"; with the embedder down the proposal is identical to 001; and a measurement test computing SC-004 (first suggestion correct for ≥ 90% of the fixture lines, against the 83% baseline of 001) plus SC-002 (0 wrong auto-accepts, 0 look-alike confusions)
- [X] T046 [US4] **Confirm RED**: run the five US4 test files; confirm they fail only because the guard, neighbor query and memory-aware matcher do not exist

### Implementation for User Story 4

- [X] T047 [US4] Add `nearest_lines(vector, model, k, min_similarity)` to `src/pedido/store.py` and the pure guard/merge functions (`token_compatible`, `may_preselect`, `merge_candidates`) to `src/pedido/memory.py`
- [X] T048 [US4] Extend `src/pedido/match.py`: the `Matcher` accepts an optional memory lookup and query vectors; only for lines already needing review it merges remembered products into the candidates and pre-selects under the guard with `motivo="memoria"`, `precisa_revisao=True`; any failure falls back to the 001 result; add `motivo_rotulo` and candidate `origem` to the line serialization in `src/pedido/web/app.py`
- [X] T049 [US4] Add the batch step to `src/pedido/chains.py`: embed all line texts in **one** call (bounded by `EMBED_TIMEOUT_SECONDS`, skipped on failure) before `match.map()`, passing the vectors to the matcher
- [X] T050 [US4] Show the reason label under a memory-suggested product and the candidate origin in `src/pedido/web/static/app.js` and `src/pedido/web/templates/index.html`; extend `scripts/run_regression_real.py` to report SC-004 against the memory fixture
- [X] T051 [US4] **Confirm GREEN**: US4 tests pass; quickstart scenarios 7 and 8 run with the fake embedder server

**Checkpoint**: memory advises, never decides; look-alikes protected.

---

## Phase 7: User Story 5 - Learn each customer's way of writing (Priority: P3)

**Goal**: similar past approved messages become few-shot examples when reading a new message.

**Independent Test**: remember messages in an unusual style, paste a new one in that style, inspect the
prompt sent to the (stub) model.

### Tests for User Story 5 (write first)

- [X] T052 [P] [US5] Write `tests/unit/test_extract_examples.py`: `build_prompt(mensagem, exemplos)` adds a pt-BR "Exemplos de mensagens anteriores e como foram lidas" section with each example's message and final lines, and with no examples returns **exactly** the 001 prompt; at most 3 examples; the store query `nearest_messages` honors model, `NULL` embeddings and `MESSAGE_MIN_SIMILARITY`; the vector input is truncated to 2,000 characters while the stored message stays whole
- [X] T053 [P] [US5] Write `tests/integration/test_examples_flow.py`: after approving messages in an unusual style, a new similar message sends a prompt containing the most similar examples (inspect the stub chat's `prompts`); with no similar message, an empty memory or a failing embedder the prompt equals the 001 prompt; the proposal still goes through matching, flags and human approval
- [X] T054 [US5] **Confirm RED**: run both US5 test files; confirm they fail only because examples are not supported yet

### Implementation for User Story 5

- [X] T055 [US5] Add `nearest_messages(vector, model, k, min_similarity)` to `src/pedido/store.py`, `retrieve_examples` to `src/pedido/memory.py`, and `exemplos` support to `build_prompt`/`extract` in `src/pedido/extract.py`
- [X] T056 [US5] Add the `embed_message | retrieve_examples` steps in front of `extract` in `src/pedido/chains.py` (one embedding call, bounded by the timeout, skipped on failure)
- [X] T057 [US5] **Confirm GREEN**: US5 tests pass; the full suite is run

**Checkpoint**: all five stories work independently.

---

## Phase 8: Polish & Cross-Cutting Concerns

- [X] T058 [P] Re-run `tests/unit/test_ptbr_strings.py` now that all new messages, labels, startup texts and UI strings exist and fix any non-pt-BR user-facing text it finds (Constitution I)
- [X] T059 [P] Update `specs/001-pedido-intake-excel/quickstart.md` and the root run instructions to point to `docker compose up -d db` and `python -m pedido`, and note in 001's research that storage moved to Postgres (feature 002)
- [X] T060 Tune the memory constants in `src/pedido/config.py` (`MEMORY_MIN_SIMILARITY`, `MEMORY_PRESELECT_SIMILARITY`, `MESSAGE_MIN_SIMILARITY`) against the T041 fixtures with a threshold sweep like 001's, keep the defaults unless the evidence says otherwise, and record the sweep and decision in `specs/002-rag-memory-providers/research.md`
- [X] T061 Run the full validation: `uv run pytest tests/unit tests/contract tests/integration` all green (001 migrated + 002); quickstart scenarios 1–10; check SC-001…SC-010 one by one and record which were verified with the fakes and which still need real services (a real LLM key, a real embeddings key, a Docker restart, Supabase later) **Status (2026-10-24):** 352 automated tests green (179 of 001 migrated + 173 new); quickstart scenarios 1–10 run against the real app and the real Postgres, with fake chat/embeddings services. **Verified with the fakes:** SC-001 (approval never fails because of the embedder, also with a stopped service), SC-002 and SC-004 with *simulated* neighbors (first suggestion 100% vs the 83% baseline; 0 wrong auto-accepts; 0 look-alike confusions, invariant across 12 threshold combinations), SC-003, SC-005, SC-006 (regression through the OpenAI-compatible adapter: same 98% / 0), SC-007 (0 keys in responses, page, OpenAPI, 21 database text columns, logs), SC-008, SC-009, SC-010; data survives a database container restart. **Still needs real services:** SC-004 and the memory thresholds with a *real* embedding model (`scripts/run_regression_real.py --memory`; the word-hash fake cannot see morphology: 5/6 with and without memory); SC-006 with a real Claude key and a real hosted OpenAI-compatible model (structured output on hosted models is unverified, research O1); embeddings on a hosted service (O2); Supabase later (RLS is enabled with no policies, untested on Supabase). **Update 2026-10-24 (real local models):** SC-004 measured with real `bge-m3` embeddings (83% → 100% on the 6-line fixture) and the regression through a real OpenAI-compatible server (`qwen2.5:14b`: 94%, 0 wrong auto-accepts); the real run found and fixed a typo-correcting behavior of the model (flag `texto_alterado`). Still pending: a real Claude key, a real hosted OpenAI-compatible model, Supabase.
- [X] T062 [P] Final cleanup: confirm no `sqlite3` import remains, no key appears in any file under `src/`, `tests/`, `scripts/`, `specs/`, `.env.example` holds no secrets, and `docker compose down` leaves the project clean

---

## Dependencies & Execution Order

### Phase dependencies

- **Setup (1)** → **Foundational (2)** → everything else. T004 (Docker + Postgres) gates every database test.
- **US1 (3)** needs Foundational (schema, `db.py`, fixtures). **US2 (4)** needs Foundational and `create_app` from US1 (T020).
- **US3 (5)** needs US1 (Postgres `Store`) and US2 (`embeddings.py`).
- **US4 (6)** and **US5 (7)** each need US3 (memory tables and rows); US4 and US5 are independent of each other.
- **Polish (8)** needs every story you ship.

### Within every phase

Test tasks → **Confirm RED** → implementation → **Confirm GREEN**. Store before services, services before
endpoints, endpoints before UI.

### Parallel opportunities

- Setup: T002, T003 together.
- Foundational tests: T005, T006, T007 together; implementation: T009, T010, T011 together (T012 after them).
- US1 tests: T014–T017 together. US2 tests: T024–T026 together; implementation T028, T029 together.
- US3 tests: T032–T034 together. US4 tests: T041–T045 together. US5 tests: T052, T053 together.
- Polish: T058, T059, T062 together.

---

## Implementation Strategy

1. **MVP = Foundational + US1 + US2** (both P1): Postgres only and providers by configuration, behavior
   identical to 001. Stop and validate after US1 (T023): the migrated 001 suite is the safety net.
2. Add **US3** (memory write, reprocess) next: it carries the highest risk to approvals, so its
   "approval never fails" tests (T034) come first.
3. Then **US4** (help in matching) and **US5** (examples when reading) in either order; both are advisory
   and degrade to 001 behavior.
4. Finish with Polish; T060 tunes the memory thresholds with evidence, not by hand per case.
