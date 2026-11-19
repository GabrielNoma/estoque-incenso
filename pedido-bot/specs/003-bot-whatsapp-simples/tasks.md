---
description: "Task list for Bot de pedidos simples (estilo WhatsApp)"
---

# Tasks: Bot de pedidos simples (estilo WhatsApp)

**Input**: Design documents from `/specs/003-bot-whatsapp-simples/`

**Prerequisites**: plan.md, spec.md, research.md, data-model.md, contracts/ (http-api, replies), quickstart.md; constitution v2.0.0

**Tests**: **REQUIRED** (Constitution II). In every phase the test tasks come first and a "confirm RED"
task proves they fail for the right reason before any implementation. Database tests run on the real
Postgres (Docker); the LLM is an injected stub or the fake OpenAI-compatible server; no internet.

**Organization**: grouped by user story. This feature **replaces** the review flow of 001/002, so the
Foundational phase also removes the obsolete modules and their tests.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: can run in parallel (different files, no dependency on an incomplete task)
- **[Story]**: US1–US6 from spec.md (none in Setup, Foundational, Polish)
- Every customer-facing text lives in `src/pedido/messages.py` and is pt-BR (Constitution I)

## Path Conventions

Single project at `/Users/gabrielmnoma/Coding/tests/project-R`: `src/pedido/`, `tests/`, `scripts/`, `assets/`.

---

## Phase 1: Setup

- [X] T001 Remove `pgvector` from `pyproject.toml` (keep `psycopg[binary]`) and run `uv sync`; pgvector is no longer used anywhere
- [X] T002 Make sure the development database is available: Docker Desktop running, `docker compose up -d db`, and `uv run python` can connect to `postgresql://pedido:pedido@localhost:5433/pedido`

**Checkpoint**: dependencies trimmed, database reachable.

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: new schema and store, simplified configuration and messages, and removal of what the new
direction drops. **No user story starts until this phase is green.**

### Tests first

- [X] T003 [P] Rewrite `tests/unit/test_db.py` for the new schema: `apply_schema` creates schema `pedido` with exactly the tables `catalog` and `pedidos`, is idempotent, enables row-level security with no policies, needs no extension; a guarded **legacy cleanup** drops `aliases`, `runs`, `run_lines`, `memoria_linhas`, `memoria_mensagens` and the `vector` extension when they exist (and does nothing when they do not); `check_database` gives the Portuguese refusal for a missing URL and for an unreachable server; no vector dimension logic remains
- [X] T004 [P] Rewrite `tests/unit/test_startup.py`: `validate_environment` refuses a missing `DATABASE_URL` and an invalid `LLM_PROVIDER` with the pt-BR messages (embeddings variables are no longer checked); `check_all` refuses an unreachable database; `python -m pedido` as a subprocess exits with code 1 and the Portuguese message without `DATABASE_URL`
- [X] T005 [P] Rewrite `tests/unit/test_store.py` for `pedidos`: `create_pedido(telefone, mensagem, itens, lista)` stores the order as `aguardando` and, in the **same transaction**, marks the phone's previous `aguardando` order `substituido`; `get_pending(telefone)` returns only the phone's waiting order; `set_estado(id, estado, resposta)` allows only `aguardando` → `confirmado` | `recusado` (a closed order never changes: raises); `itens` round-trips as JSON; a new `Store` instance sees the data (restart); two phone numbers never interfere; a failing write leaves nothing half-saved
- [X] T006 [P] Update `tests/conftest.py`: remove the embedder fixture and the old table list (`TABLES` becomes `pedidos`, `catalog`); keep `database_url`, `clean_db`, `scratch_database_url`, `openai_server`, `stub_chat`; the old `client` fixture is replaced in Phase 8
- [X] T007 [P] Update `tests/unit/test_fakes.py`: remove the `FakeEmbedder` tests and the `/v1/embeddings` test; keep the fake chat server tests (responder, fixed port, error mode)
- [X] T008 **Confirm RED**: run `uv run pytest tests/unit/test_db.py tests/unit/test_startup.py tests/unit/test_store.py tests/unit/test_fakes.py`; confirm they fail only because the new schema, store and messages do not exist yet

### Implementation

- [X] T009 [P] Simplify `src/pedido/config.py`: keep paths, `database_url()`, the `llm_*` accessors and `MODEL_NAME`; remove the fuzzy thresholds, `CANDIDATE_MIN_SCORE`, `TIE_BREAK_WINDOW`, `LOW_CONFIDENCE`, every `EMBED_*` and `MEMORY_*` setting
- [X] T010 [P] Rewrite `src/pedido/messages.py` with the exact replies of `contracts/replies.md` (`PERGUNTA_CONFIRMACAO`, `CONFIRMADO`, `CANCELADO`, `ENVIE_PEDIDO`, `SEM_ITENS`, `ERRO_LEITURA`, `ERRO_PLANILHA`, `ERRO_BANCO`), the startup messages for the database and the provider, the HTTP error codes of `contracts/http-api.md`, and the chat page labels; remove every message of the old flow (flags, memory, reprocess, embeddings)
- [X] T011 Rewrite `src/pedido/schema.sql` (tables `catalog` and `pedidos`, index, RLS, no extension, guarded legacy cleanup), simplify `src/pedido/db.py` (no `pgvector`, no dimension) and `src/pedido/startup.py`, and rewrite `src/pedido/store.py` for `pedidos` as specified in T003–T005
- [X] T012 Update `tests/fakes.py`: remove `FakeEmbedder` and the `/v1/embeddings` route
- [X] T013 Delete the obsolete code and tests of 001/002: `src/pedido/validate.py`, `memory.py`, `reprocess.py`, `embeddings.py`; unit tests `test_alias_learning.py`, `test_embeddings.py`, `test_extract_examples.py`, `test_match_memory.py`, `test_match_regression.py`, `test_memory_guard.py`, `test_memory_neighbors.py`, `test_memory_write.py`, `test_reprocess.py`, `test_validate.py`; all contract tests (`tests/contract/test_api_*.py`); integration tests `test_examples_flow.py`, `test_extraction_fidelity.py`, `test_memory_flow.py`, `test_proposal_chain.py`; and `tests/memhelpers.py`
- [X] T014 **Confirm GREEN**: `uv run pytest tests/unit/test_db.py tests/unit/test_startup.py tests/unit/test_store.py tests/unit/test_fakes.py tests/unit/test_ptbr_strings.py`; start the app code path that applies the schema once against the development database so the legacy tables are cleaned

**Checkpoint**: new schema applied, store works, obsolete features gone.

---

## Phase 3: User Story 1 - Receive the organized list (Priority: P1) 🎯

**Goal**: an order text becomes the plain list (closest product, summed, Excel order) ending in `ok ou não?`.

**Independent Test**: send messages with several items, repeated products, abbreviations and typos; the
reply is only the list in form order with summed quantities and the closing line.

### Tests for User Story 1 (write first)

- [X] T015 [P] [US1] Add to `tests/unit/test_normalize.py` and `tests/unit/test_catalog.py`: `normalize_variants("7 Linhas")` gives `["7 linhas", "sete linhas"]`; the products "7 Linhas", "7 Forças" and "7 Giras" each have both forms; no two products share an exact form (collision check still holds)
- [X] T016 [P] [US1] Rewrite `tests/unit/test_match.py` for `Matcher.closest(text)`: an exact wording wins (catalog name, abbreviation `abre c. da felicidade`, the full wordings of `S.` as santo/santa/saúde, `sete linhas`) and never loses to a similar product ("abre caminho" is Abre Caminho, never Abre C. da Felicidade); a typo goes to the closest ("abre camino" → Abre Caminho, "descarrego completto" → Descarrego Completo); nonsense still returns a product (no floor); ties go to the first product in Excel order; text that normalizes to nothing returns `None`; there is no `precisa_revisao`, candidates, alias or LLM tie-break
- [X] T017 [P] [US1] Write `tests/unit/test_lista.py`: `aggregate` sums quantities by product, orders by `(bloco, linha)` (Excel order), drops quantities ≤ 0; `formatar_quantidade` gives `2`, `0,5`, `2,25`; `renderizar` gives one `<Produto> — <q> dz` line per product, a blank line and `ok ou não?`, exactly and nothing else
- [X] T018 [P] [US1] Rewrite `tests/unit/test_extract.py` for the simplified schema `{texto, quantidade}` (quantidade defaults to 1): the prompt is pt-BR, tells the model to copy the customer's text, to convert units to dozens ("12 unidades" = 1 dúzia, "meia dúzia" = 0.5) and that a missing quantity is 1; the model is injected; a failure or malformed answer is retried exactly once and a second failure raises `ExtractionFailed`; an empty list is a valid result
- [X] T019 [P] [US1] Rewrite the regression fixtures: `tests/fixtures/mensagens/expected.json` becomes `{"mensagens": [{"arquivo", "linhas": [{"texto", "quantidade", "produto"}]}]}` where `produto` is the intended product (or `null` when no product is intended, such as "incenso de lavanda azul"), keeping the 22 message files; update `tests/fixtures/llm_stubs/extracoes.json` to drop the `unidade` field
- [X] T020 [P] [US1] Write `tests/integration/test_order_chain.py`: the chain `extract | match | aggregate` over every regression message with the stubbed extraction yields the expected products, sums repeated products and follows the Excel order; the share of lines with an intended product that end on it is **at least 90%**; exact wordings are 100% correct
- [X] T021 [P] [US1] Write `tests/unit/test_conversa_pedido.py`: `interpretar` returns `ok` / `nao` / `pedido` for the whole message, ignoring case, accents and punctuation (ok, okay, sim, s, confirmo, confirmado, isso, certo, blz, pode, beleza; não, nao, n, cancelar, cancela, errado, negativo; "ok obrigado" and "2 dz ogum" are orders); `Conversa.responder(telefone, texto)` for an order returns a reply that is exactly the list plus `ok ou não?` (no question, remark or marker), no file, and stores the order as `aguardando`
- [X] T022 [US1] **Confirm RED**: run the US1 test files; confirm they fail only because `closest`, `lista.py`, the new extract schema, the order chain and `conversa.py` do not exist yet

### Implementation for User Story 1

- [X] T023 [P] [US1] Add `"7": ["sete"]` to `assets/abbreviations.json` `variantes`
- [X] T024 [US1] Rewrite `src/pedido/match.py`: `Matcher(catalog)` with `closest(text) -> Product | None` (exact forms first, otherwise the best `token_sort_ratio` over all forms of all products, ties by Excel order, no floor) and the `runnable()` per-line map; remove aliases, candidates, memory and LLM tie-break
- [X] T025 [P] [US1] Simplify `src/pedido/extract.py` to `LinhaExtraida{texto, quantidade=1.0}`, the new pt-BR prompt (unit conversion, default quantity, copy the text) and the retry/`ExtractionFailed`; remove examples and the unit field
- [X] T026 [P] [US1] Create `src/pedido/lista.py` (`aggregate`, `formatar_quantidade`, `renderizar`) as in T017
- [X] T027 [US1] Rewrite `src/pedido/chains.py`: `build_order_chain(matcher, chat_model)` = `extract | match.map | aggregate` (LCEL), returning `[(Product, quantity)]` in Excel order; keep `build_export_chain`; remove every old chain
- [X] T028 [US1] Create `src/pedido/conversa.py` with `interpretar` and the **order path** of `Conversa.responder` (read → render → `store.create_pedido`), returning a `Resposta(texto, arquivo_nome=None, arquivo_bytes=None, pedido_id)`
- [X] T029 [US1] **Confirm GREEN**: US1 tests pass; run the regression chain test and note the measured accuracy

**Checkpoint**: an order text yields the exact list reply; the engine stores it as waiting.

---

## Phase 4: User Story 2 - Confirm with "ok" and receive the Excel (Priority: P1) 🎯

**Goal**: ok generates the Excel with the confirmed quantities; nothing is generated before ok.

**Independent Test**: send an order, answer ok, open the returned file.

### Tests for User Story 2 (write first)

- [X] T030 [P] [US2] Write `tests/unit/test_conversa_confirmacao.py`: ok (any accepted word) with a pending order returns `CONFIRMADO` plus the file bytes and name `pedido-<id>.xlsx`, and the order becomes `confirmado` with `resposta` and `respondido_em` set; **no file is generated before ok** (spy on `fill_template`: zero calls after the order message and after other texts); the file has every quantity in the cell of its product, the 189 formulas intact, the header cells empty and the template untouched (reuses the checks of `test_export.py`); a second ok gets `ENVIE_PEDIDO` and no file; ok with nothing pending gets `ENVIE_PEDIDO`
- [X] T031 [US2] **Confirm RED**: run `tests/unit/test_conversa_confirmacao.py`; confirm it fails only because the ok path is missing

### Implementation for User Story 2

- [X] T032 [US2] Extend `src/pedido/conversa.py` with the **ok path**: take the pending order, generate the Excel through the export chain, then mark it `confirmado`; return the file in the `Resposta`
- [X] T033 [US2] **Confirm GREEN**: US2 tests pass; the existing `tests/unit/test_export.py` still passes unchanged

**Checkpoint**: P1 stories done: list, then ok, then Excel.

---

## Phase 5: User Story 3 - Say "não" or send something else (Priority: P2)

**Goal**: não discards the pending order; other text replaces it; neutral replies when nothing is pending.

### Tests for User Story 3 (write first)

- [X] T034 [P] [US3] Write `tests/unit/test_conversa_recusa.py`: não (any accepted word) with a pending order replies `CANCELADO` and the order becomes `recusado`; não with nothing pending replies `ENVIE_PEDIDO`; a new order text while one is pending replies with the new list, the previous order becomes `substituido`, and a later ok confirms **only** the new one; the reply to a message with no items (or an empty text) is `SEM_ITENS` and the pending order is kept
- [X] T035 [US3] **Confirm RED**: run `tests/unit/test_conversa_recusa.py`

### Implementation for User Story 3

- [X] T036 [US3] Extend `src/pedido/conversa.py` with the não path, the replacement of the pending order and the `SEM_ITENS` reply
- [X] T037 [US3] **Confirm GREEN**: US3 tests pass

**Checkpoint**: the whole conversation works in memory-free tests.

---

## Phase 6: User Story 4 - The pending order survives a restart (Priority: P2)

**Goal**: orders are stored per phone number; "ok" works after a restart.

### Tests for User Story 4 (write first)

- [X] T038 [P] [US4] Write `tests/unit/test_conversa_persistencia.py`: a new `Conversa` (and `Store`) built on the same database after an order message still confirms with ok; two phone numbers with pending orders confirm independently and never see each other's list; each stored order has the message, the list sent, the answer and the state; nothing is written to local files other than the delivered file (run inside an empty temporary directory and check it stays empty)
- [X] T039 [US4] **Confirm RED** (it may already pass because of the store tests; if so, note it and keep the tests as guards)

### Implementation for User Story 4

- [X] T040 [US4] Make the tests pass (the engine only reads and writes through `Store`, never keeps state in memory); fix anything they reveal in `src/pedido/conversa.py` or `src/pedido/store.py`
- [X] T041 [US4] **Confirm GREEN**: US4 tests pass; the refusal-to-start tests of Phase 2 (T004) still pass

**Checkpoint**: restart-safe conversations.

---

## Phase 7: User Story 5 - Failures are short and neutral (Priority: P2)

**Goal**: any failure becomes one short neutral sentence; the pending order is never lost; the engine never raises.

### Tests for User Story 5 (write first)

- [X] T042 [P] [US5] Write `tests/unit/test_conversa_falhas.py`: the model failing twice or an unconfigured provider (`LLMNotConfigured`) replies `ERRO_LEITURA` and keeps the pending order; a failing Excel generation replies `ERRO_PLANILHA`, the order stays pending and a later ok sends the file; a database error (`psycopg.OperationalError` from the store) replies `ERRO_BANCO` and leaves nothing half-saved; any unexpected exception becomes `ERRO_BANCO`-style neutral reply instead of propagating; no reply ever contains a key
- [X] T043 [US5] **Confirm RED**: run `tests/unit/test_conversa_falhas.py`

### Implementation for User Story 5

- [X] T044 [US5] Make `Conversa.responder` catch `ExtractionFailed`/`LLMNotConfigured`, export failures and database errors and turn each into the matching reply of `messages.py`, keeping the pending order
- [X] T045 [US5] **Confirm GREEN**: US5 tests pass

**Checkpoint**: the bot is predictable when a service is down.

---

## Phase 8: User Story 6 - The simple chat page and the API (Priority: P2)

**Goal**: a very simple pt-BR chat page and the HTTP endpoints over the engine.

### Tests for User Story 6 (write first)

- [X] T046 [P] [US6] Replace the `client` fixture in `tests/conftest.py` with one built on `create_app(database_url, chat_model)` and the real test database, and write `tests/contract/test_api_mensagem.py` per `contracts/http-api.md`: `POST /api/mensagem` returns `{resposta, arquivo}`; an order gets the exact list reply with `arquivo` null; ok returns the file reference and `GET /api/pedidos/{id}/planilha` returns an `.xlsx` regenerated from the stored items; the file endpoint answers `404 pedido_nao_encontrado` and `409 pedido_nao_confirmado` with pt-BR messages; missing fields give `422 requisicao_invalida`; the home page is served in Portuguese with the phone field, the message box and the send button; through the OpenAI-compatible adapter pointed at the fake server a full conversation works and the key never appears in any response, in the stored orders or in the OpenAPI document
- [X] T047 [US6] **Confirm RED**: run `tests/contract/test_api_mensagem.py`

### Implementation for User Story 6

- [X] T048 [US6] Rewrite `src/pedido/web/app.py`: `create_app(database_url=None, chat_model=None, template_path=None)` builds the store, the catalog, the matcher and the `Conversa`; `POST /api/mensagem`, `GET /api/pedidos/{id}/planilha`, `GET /`; the pt-BR error handlers for 404/409/422 and an unexpected error; remove every old endpoint and the embedder wiring
- [X] T049 [US6] Rewrite the page: `src/pedido/web/templates/index.html`, `src/pedido/web/static/app.js`, `src/pedido/web/static/app.css` as a very simple chat (phone number field, chat bubbles, message box, send button, the Excel shown as a download link); all text from `messages.py`
- [X] T050 [US6] **Confirm GREEN**: US6 tests pass; drive the page in a browser with a stubbed model and with the local Ollama: quickstart scenarios 1–7

**Checkpoint**: the whole bot can be tried in the browser.

---

## Phase 9: Polish & Cross-Cutting Concerns

- [X] T051 [P] Rewrite `scripts/run_regression_real.py`: run the 22 regression messages through the order chain (offline with the canned extractions, or `--real` with `--provider/--model/--base-url`) and print the share of lines that end on the intended product (target ≥ 90%) and the exact-wording accuracy (target 100%); remove the memory and review logic
- [X] T052 [P] Update `.env.example` (remove `EMBED_*`), `docker-compose.yml` comment (pgvector not required), `.env`, and add the update notices to `specs/002-rag-memory-providers/` and `specs/001-pedido-intake-excel/` (superseded in part by 003)
- [X] T053 [P] Re-run `tests/unit/test_ptbr_strings.py` with the new messages and page; fix any non-pt-BR text (Constitution I)
- [X] T054 Run the full validation: `uv run pytest` all green; quickstart scenarios 1–10 on the real app with the local Ollama (`qwen2.5:14b`); record the measured accuracy of the regression with the real model in `research.md`
- [X] T055 [P] Final cleanup: no `sqlite3`, `pgvector`, `embed` or `memoria` left in `src/`, `tests/`, `scripts/`; no key in any file; `.env.example` holds no secrets

---

## Dependencies & Execution Order

- **Setup (1)** → **Foundational (2)** → every story. T002 gates every database test.
- **US1 (3)** needs Foundational. **US2 (4)** needs US1 (it extends `conversa.py`). **US3 (5)** needs US2.
- **US4 (6)** and **US5 (7)** each need US3. **US6 (8)** needs US5 (the page shows the same replies).
- **Polish (9)** needs every story.
- Within a phase: tests → **Confirm RED** → implementation → **Confirm GREEN**.
- The old `web/app.py` imports removed modules and is broken from T013 until T048; nothing in between
  imports it (the startup refusal test exits before the import).

### Parallel opportunities

- Setup: none. Foundational tests: T003–T007 together; implementation T009, T010 together.
- US1 tests: T015–T021 together; implementation T023, T025, T026 together.
- US2–US5 each have one test file; Polish: T051–T053, T055 together.

---

## Implementation Strategy

1. **MVP = Foundational + US1 + US2**: the engine already turns an order into the list and, after ok, into
   the Excel (tested without any page). Stop and validate after US2 (T033).
2. Add US3, US4, US5 (still engine-only tests), then US6 to put the conversation in the browser.
3. Finish with the regression run on the real local model (T054); the real WhatsApp adapter is the next
   feature and will call `Conversa.responder` directly.
