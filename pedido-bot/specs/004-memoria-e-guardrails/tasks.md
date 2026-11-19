---
description: "Task list for Memória silenciosa de apelidos e guardrails"
---

# Tasks: Memória silenciosa de apelidos e guardrails

**Input**: Design documents from `/specs/004-memoria-e-guardrails/`

**Prerequisites**: plan.md, spec.md, research.md, data-model.md, contracts/ (configuration, replies, script), quickstart.md; constitution v2.1.0

**Tests**: **REQUIRED** (Constitution II). In every phase the test tasks come first and a "confirm RED" task proves they fail for the right reason before any implementation. Database tests run on the real Postgres with pgvector (Docker); the chat model and the embedder are injected stubs, or the fake OpenAI-compatible server (chat and embeddings); no internet.

**Organization**: grouped by user story. The Foundational phase prepares the database, the embedder and the fakes that every story needs.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: can run in parallel (different files, no dependency on an incomplete task)
- **[Story]**: US1–US5 from spec.md (none in Setup, Foundational, Polish)
- Every customer-facing text lives in `src/pedido/messages.py` and is pt-BR (Constitution I)

## Path Conventions

Single project at `/Users/gabrielmnoma/Coding/tests/project-R`: `src/pedido/`, `tests/`, `scripts/`.

---

## Phase 1: Setup

- [X] T001 Add the `pgvector` Python adapter (`uv add pgvector`) and confirm `import pgvector.psycopg` works
- [X] T002 [P] Write `tests/unit/test_config_limits.py`: the settings of `contracts/configuration.md` have the documented defaults (`MAX_LINHAS` 50, `MAX_TEXTO_LINHA` 120, `MAX_MENSAGEM` 2000, `LIMITE_MSG_POR_MINUTO` 20, `MAX_QTD_PRODUTO` 1000, `EMBED_TIMEOUT_SECONDS` 5, `EMBED_SIMILARITY` 0.92, `EMBED_DIMENSIONS` 1024), are read from the environment at call time, and an invalid number falls back to the default
- [X] T003 Add the limit and `EMBED_*` readers to `src/pedido/config.py` and the new constants to `src/pedido/messages.py` (`MENSAGEM_LONGA`, `MUITAS_MENSAGENS`, `QUANTIDADE_ALTA`, `ERRO_VECTOR_INDISPONIVEL`, `ERRO_DIMENSAO_DIFERENTE`, `APELIDO_NAO_ENCONTRADO`, the script headers) with the texts of `contracts/replies.md`; run T002 and `tests/unit/test_ptbr_strings.py`

**Checkpoint**: settings and messages exist.

---

## Phase 2: Foundational (blocks every story)

### Tests (write first)

- [X] T004 [P] Extend `tests/unit/test_db.py`: `apply_schema(url, dimensions)` creates the `vector` extension, the table `apelidos` with the unique pair, `pedidos.linhas`, and RLS; it is idempotent; a database that already holds 003 data (orders) keeps every order; `apelidos` created with 1024 and checked with 768 raises `StartupError` carrying `ERRO_DIMENSAO_DIFERENTE`; the 003 cleanup no longer drops the `vector` extension; `check_database` without the extension available raises `ERRO_VECTOR_INDISPONIVEL`
- [X] T005 [P] Write `tests/unit/test_store_apelidos.py` on the real database: `upsert_positivo` creates then increments, stores `embedding` and `modelo` (null allowed); `penalizar` only increments existing rows and never creates or deletes; the **applies** rule (`ativo`, `positivos >= 2`, `positivos > negativos`) in `buscar_exato(texto_normalizado)`; `buscar_similar(vector, modelo, limiar)` returns the best applying product above the threshold, ignores other models, null embeddings, disabled and non-applying rows; ties by `positivos - negativos` then Excel order; `set_status`, `list_apelidos`; `create_pedido(..., linhas=[...])` round-trips `linhas`
- [X] T006 [P] Write `tests/unit/test_embeddings.py`: `build_embedder(env)` returns `None` without `EMBED_BASE_URL`/`EMBED_MODEL`; with them, `embed(text)` calls the fake OpenAI-compatible server with the model, the key as bearer, and returns the vector; a slow server beyond `EMBED_TIMEOUT_SECONDS` and an HTTP error raise `EmbeddingFailed`; a vector of another size raises `EmbeddingFailed`; the key never appears in `repr`
- [X] T007 [P] Extend `tests/fakes.py` (embeddings route of `FakeOpenAIServer` with `embed_vectors`/`embed_delay`/`fail_status`, and a `FakeEmbedder` returning vectors from a given table, otherwise a deterministic hash vector) and `tests/conftest.py` (`embed_dimensions`, `embedder` fixtures, `apelidos` in the truncated tables); cover the fakes in `tests/unit/test_fakes.py`
- [X] T008 **Confirm RED**: run T004–T007; confirm they fail only because the schema, store methods, `embeddings.py` and the fake routes do not exist yet

### Implementation

- [X] T009 [P] Update `src/pedido/schema.sql` and `src/pedido/db.py`: `create extension if not exists vector`, table `apelidos` built with the configured dimension (template the `vector(N)` in `apply_schema`), unique pair, indexes (exact text; HNSW cosine), RLS, `pedidos.linhas`, no more `drop extension`; `check_database(url, dimensions)` raises the Portuguese errors; update `src/pedido/startup.py` to read `EMBED_DIMENSIONS`
- [X] T010 [P] Create `src/pedido/embeddings.py` (`Embedder`, `EmbeddingFailed`, `build_embedder(env)`) over `langchain_openai.OpenAIEmbeddings` (`check_embedding_ctx_length=False`), with the timeout and dimension check
- [X] T011 Extend `src/pedido/store.py` with the `apelidos` methods of T005 and `linhas` in `create_pedido`/`get_pedido`/`get_pending`; register the pgvector adapter on each connection
- [X] T012 **Confirm GREEN**: T004–T007 pass; the whole 003 suite still passes

**Checkpoint**: the database, the store and the embedder work in isolation.

---

## Phase 3: User Story 1 - The bot learns the customers' own wording (Priority: P1)

**Goal**: ok teaches, a learned nickname changes matching, nothing shows in the reply.

**Independent Test**: confirm a wording twice, send a similar wording, see the product; replies stay identical.

### Tests (write first)

- [X] T013 [P] [US1] Rewrite the matcher tests in `tests/unit/test_match.py` for an injected `apelidos` lookup: order exact → nickname → closest; a nickname never overrides an exact wording; a lookup returning `None` or raising falls back to the closest; without a lookup behaves as 003
- [X] T014 [P] [US1] Write `tests/unit/test_memoria.py` on the real database with `FakeEmbedder`: `buscar(texto)` by exact normalized text, then by similarity above `EMBED_SIMILARITY` (below it: nothing); other model ignored; a failing embedder returns `None` without raising and is skipped for the rest of the message (one failure, no further calls); no embedder call when no nickname exists for the model; `aprender(linhas)` stores only non-exact lines with `positivos + 1` and the embedding, and stores the row without embedding when the embedder fails; a wording confirmed once does not apply, twice does; a database error never raises
- [X] T015 [P] [US1] Write `tests/unit/test_conversa_memoria.py` with an inline executor: two confirmed orders for "abre c felicidade" then a similar wording ("abre c da felicidade") goes to the product even when plain similarity prefers another (vectors from the table); one confirmation is not enough; an exact wording of another product wins; the replies of every scenario are **byte-for-byte equal** to those of a `Conversa` without memory, apart from the changed product; the memory is written after the reply (the reply is returned before the executor runs the write); a failing store or embedder never changes the reply or the file; without an embedder the behavior is exactly 003; no reply or file contains the words "apelido" or "memória"
- [X] T016 [P] [US1] Update `tests/integration/test_order_chain.py` for the new chain result (`.itens` as before and `.linhas` with wording, quantity and product id per line) and keep the ≥ 90% and exact-wording checks
- [X] T017 [US1] **Confirm RED**: run T013–T016; confirm they fail only because `Matcher(apelidos=...)`, `memoria.py`, the chain result and the conversation hooks do not exist

### Implementation

- [X] T018 [US1] `src/pedido/match.py`: `Matcher(catalog, abbreviations, apelidos=None)`; `closest` tries exact → `apelidos(texto_normalizado)` (any exception ignored) → closest
- [X] T019 [US1] `src/pedido/chains.py` and `src/pedido/lista.py`: the order chain returns a `ResultadoPedido(itens, linhas)` (aggregated items plus the matched lines); update the callers in `conversa.py` and `scripts/run_regression_real.py`
- [X] T020 [US1] Create `src/pedido/memoria.py`: `Memoria(store, embedder, executor=None)` with `buscar` (per-message circuit breaker), `aprender`, `penalizar`, and `agendar(fn)` on a single-worker executor; every error is swallowed and logged by type only
- [X] T021 [US1] `src/pedido/conversa.py`: `Conversa(..., memoria=None)` passes `memoria.buscar` to the matcher, stores `linhas` with the order, and after an ok schedules `aprender` (non-exact lines only) once the reply is built
- [X] T022 [US1] **Confirm GREEN**: US1 tests pass; the 003 suite still passes

**Checkpoint**: learning works end to end in engine tests.

---

## Phase 4: User Story 2 - Negative answers weaken, never erase (Priority: P1)

**Goal**: não and replacement add negatives; a nickname stops and resumes by the rule.

### Tests (write first)

- [X] T023 [P] [US2] Write `tests/unit/test_conversa_sinais.py`: a nickname with 2 positives and two orders ending in não or replaced stops applying (matching falls back); one more confirmation applies it again; nothing is ever deleted (row counts unchanged); only the lines of the refused or replaced order are penalized and only for wordings that already exist; refused orders never create wordings; a reply is never affected
- [X] T024 [US2] **Confirm RED**: run T023

### Implementation

- [X] T025 [US2] `src/pedido/conversa.py`: after não and after a replacement schedule `penalizar` for the lines of that order
- [X] T026 [US2] **Confirm GREEN**: US2 tests pass

**Checkpoint**: the learning corrects itself.

---

## Phase 5: User Story 3 - The embedding service is configurable and safe to lose (Priority: P1)

**Goal**: configured by environment, short timeout, silent fallback, the app wires it.

### Tests (write first)

- [X] T027 [P] [US3] Write `tests/contract/test_api_memoria.py`: `create_app` builds the embedder from the environment (fake server) and a full conversation through the HTTP API with the fake chat **and** embedding server learns a nickname after two confirmations and applies it; with the embedding server slow beyond the timeout or down, orders still get their list and ok its file within the limit plus a margin and with no error text; without `EMBED_*` the app behaves as 003; an old 003 database is upgraded at startup keeping its orders; the key never appears in any response, the OpenAPI document, the stored rows or the logs
- [X] T028 [US3] **Confirm RED**: run T027

### Implementation

- [X] T029 [US3] `src/pedido/web/app.py`: build the embedder with `build_embedder()` (parameter `embedder` for tests), the `Memoria`, pass the dimension to `check_database`, and give the `Conversa` its memory
- [X] T030 [US3] **Confirm GREEN**: US3 tests pass; run the learning flow against the real Ollama `bge-m3` once and note the similarity values of the sample wordings in `research.md` D5 (calibration of `EMBED_SIMILARITY`)

**Checkpoint**: the memory runs in the app and fails softly.

---

## Phase 6: User Story 4 - The model can only be used to read orders (Priority: P1)

**Goal**: data-not-instructions prompt, validated output, 1000 dz cap, size and rate limits, type-only logs.

### Tests (write first)

- [X] T031 [P] [US4] Write `tests/unit/test_guardrails.py`: `validar_linhas` drops lines beyond `MAX_LINHAS`, texts above `MAX_TEXTO_LINHA` or empty, and quantities that are zero, negative, NaN, infinite, boolean or not numbers; `checar_quantidade` accepts exactly 1000 and refuses 1001 of one product (not the sum of different products); `checar_tamanho`; `RateLimiter` with an injected clock (21st message in 60 s refused, the window slides, numbers are independent); `registrar(tipo)` logs only the type (use `caplog`: no text, no phone number)
- [X] T032 [P] [US4] Extend `tests/unit/test_extract.py`: the prompt delimits the message with fixed markers and states that instructions inside it are ignored; the memory/nicknames are never part of the prompt; the extraction result passes through `validar_linhas`
- [X] T033 [P] [US4] Write `tests/unit/test_conversa_guardrails.py`: a message with embedded instructions keeps the reply format (list plus `ok ou não?`, or `SEM_ITENS`) and contains none of the injected content (stub model returning hostile text in `texto` is shown only as a product match, never echoed); 5000 dz of one product → `QUANTIDADE_ALTA`, no list, no new pending order, the previous pending order kept and nothing remembered; exactly 1000 dz is accepted; a long message → `MENSAGEM_LONGA` and the model is **not** called (stub with no canned answer); the 21st message in a minute → `MUITAS_MENSAGENS`, ignored, other numbers unaffected; ok and não are not blocked by the size limit; guardrail logs hold only types
- [X] T034 [US4] **Confirm RED**: run T031–T033

### Implementation

- [X] T035 [P] [US4] Create `src/pedido/guardrails.py` (`validar_linhas`, `checar_quantidade`, `checar_tamanho`, `RateLimiter`, `registrar`)
- [X] T036 [P] [US4] `src/pedido/extract.py`: the delimited, data-not-instructions prompt and the validation of the model output
- [X] T037 [US4] `src/pedido/conversa.py`: rate limit first, size check before the model, quantity cap after summing (nothing stored, pending kept), constant replies, `registrar` on every activation
- [X] T038 [US4] **Confirm GREEN**: US4 tests pass; the whole suite passes

**Checkpoint**: the model is fenced.

---

## Phase 7: User Story 5 - See and switch off nicknames with a script (Priority: P3)

**Goal**: a small Portuguese command-line tool.

### Tests (write first)

- [X] T039 [P] [US5] Write `tests/unit/test_script_apelidos.py` on the real database: the list shows id, wording, product name, positives, negatives, status and "aplica" (sim/não); `--desativar ID` stops it applying and deletes nothing; `--ativar ID` brings it back when the rule allows; an unknown id prints `APELIDO_NAO_ENCONTRADO`, exit code 1, changes nothing; all output is pt-BR
- [X] T040 [US5] **Confirm RED**: run T039

### Implementation

- [X] T041 [US5] Create `scripts/apelidos.py` with a testable `main(argv, url)` as in `contracts/script.md`
- [X] T042 [US5] **Confirm GREEN**: US5 tests pass

**Checkpoint**: nicknames can be inspected and undone.

---

## Phase 8: Polish & Cross-Cutting Concerns

- [X] T043 [P] Restore the `EMBED_*` and limit variables (commented, no secrets) in `.env.example`; set `EMBED_*` for local Ollama in `.env`; update the `docker-compose.yml` comment (pgvector required again)
- [X] T044 [P] Re-run `tests/unit/test_ptbr_strings.py` including the new messages and the script output; fix anything not pt-BR
- [X] T045 [P] Add a short update note to `specs/003-bot-whatsapp-simples/spec.md` (extended by 004: memory and guardrails)
- [X] T046 Run the full validation: `uv run pytest` all green; quickstart scenarios 1–9 on the real app with Ollama (`qwen2.5:14b`, `bge-m3`); record the calibration of `EMBED_SIMILARITY` and the regression accuracy in `research.md`
- [X] T047 [P] Final cleanup: no key in any file; no message text or phone number in any log line; `.env.example` holds no secrets

---

## Dependencies & Execution Order

- **Setup (1)** → **Foundational (2)** → every story.
- **US1 (3)** needs Foundational. **US2 (4)** needs US1 (extends `conversa.py`). **US3 (5)** needs US1. **US4 (6)** needs US1 (extends `conversa.py` and `extract.py`). **US5 (7)** needs Foundational (store).
- **Polish (8)** needs every story.
- Within a phase: tests → **Confirm RED** → implementation → **Confirm GREEN**.

### Parallel opportunities

- Foundational tests T004–T007 together; implementation T009, T010 together.
- US1 tests T013–T016 together. US4 tests T031–T033 together; implementation T035, T036 together.
- Polish T043–T045, T047 together.

---

## Implementation Strategy

1. **Stop point for the owner's validation = Foundational + US1 + US2 + US3**: embeddings and the nickname memory working end to end through the app (T030). The guardrails (US4) and the script (US5) follow.
2. Calibrate the similarity threshold with the real `bge-m3` model at T030 before trusting the default.
3. The service API for the stock system and the WhatsApp adapter are later features.
