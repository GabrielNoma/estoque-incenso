---
description: "Task list for Modelo de planilha gerenciado"
---

# Tasks: Modelo de planilha gerenciado

**Input**: Design documents from `/specs/005-modelo-planilha/`

**Prerequisites**: plan.md, spec.md, research.md, data-model.md, contracts/ (http-api, replies), quickstart.md; constitution v2.2.0

**Tests**: **REQUIRED** (Constitution II). Test tasks come first and a "confirm RED" task proves they fail for the right reason before any implementation. Database tests run on the real Postgres with pgvector (Docker); model files are built in tests with openpyxl from the seed; no network.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: can run in parallel (different files, no dependency on an incomplete task)
- **[Story]**: US1–US5 from spec.md (none in Setup, Foundational, Polish)
- Every user-facing text lives in `src/pedido/messages.py` and is pt-BR (Constitution I)

---

## Phase 1: Setup

- [X] T001 [P] Add `max_modelo_mb()` (`MAX_MODELO_MB`, default 5) to `src/pedido/config.py` with a case in `tests/unit/test_config_limits.py`
- [X] T002 [P] Add the constants of `contracts/replies.md` to `src/pedido/messages.py` (`MODELO_INVALIDO`, `MODELO_PRODUTO_AUSENTE`, `MODELO_VAZIO`, `MODELO_XLS`, `MODELO_ILEGIVEL`, `MODELO_SEM_PRODUTOS`, `MODELO_NOME_REPETIDO`, `MODELO_CELULA_MESCLADA`, `MODELO_GRANDE`, the errors `modelo_invalido`/`modelo_grande` in `ERROS`); run `tests/unit/test_ptbr_strings.py`
- [X] T003 Create `tests/modelos_helpers.py`: build model variants from the seed bytes with openpyxl (`com_produto_novo`, `sem_produto`, `renomeado`, `nome_repetido`, `celula_mesclada`, `vazio`, `xls_antigo`, `lixo`); add the fixtures `modelo_bytes`, `variante` to `tests/conftest.py`

---

## Phase 2: Foundational (blocks every story)

### Tests (write first)

- [X] T004 [P] Extend `tests/unit/test_catalog.py` and write `tests/unit/test_validar_modelo.py`: `load_catalog` accepts bytes and gives the same catalog as the path; `validar_modelo` returns the catalog for the seed and for a model with a new product; each refusal gives its constant message (empty, `.xls` signature, garbage, no products, repeated name quoted, merged quantity cell named); a size above the limit is refused by the caller's check
- [X] T005 [P] Extend `tests/unit/test_export.py`: `fill_template` accepts bytes; the result of a model with a new product has the quantity in that product's cell; `quantities_for_export` raises `ProdutoAusente` for a product id that is not in the catalog (it no longer drops silently)
- [X] T006 [P] Extend `tests/unit/test_db.py`: the schema creates `modelos` (unique `versao`, at most one active), `pedidos.modelo_versao`, `apelidos.produto_nome`; a 004 database is upgraded keeping orders and nicknames
- [X] T007 [P] Write `tests/unit/test_store_modelos.py`: `salvar_modelo` stores the bytes, makes the new version active and the old inactive in one transaction, versions increase, nothing is deleted, a failure keeps the previous active; `modelo_ativo`, `versao_ativa`, `get_modelo(versao)`, `listar_modelos`; `set_estado(..., modelo_versao=...)` records the version; `upsert_positivo(..., produto_nome=...)`; `sincronizar_apelidos(catalog)` fills missing names, disables (never deletes) nicknames whose product is missing or renamed and keeps the unchanged ones active
- [X] T008 [P] Write `tests/unit/test_modelos_service.py`: the seed is installed as version 1 once; `atual()` returns the catalog of the active model and rebuilds only when the version changes (also when another connection activates one); `importar(bytes, arquivo)` validates, activates, returns the summary (version, file, products, added, removed, renamed, nicknames disabled) and an invalid file changes nothing; a model that cannot be read or has no products raises `ModeloIndisponivel`; `por_versao`
- [X] T009 **Confirm RED**: run T004–T008; they fail only because the code does not exist yet

### Implementation

- [X] T010 [P] `src/pedido/catalog.py`: `load_catalog` accepts bytes; `ModeloInvalido`; `validar_modelo(conteudo, abbreviations)`; `src/pedido/export.py`: bytes template and `ProdutoAusente`; `src/pedido/chains.py` passes the template through
- [X] T011 [P] `src/pedido/schema.sql`: table `modelos` with the unique partial index and RLS, `pedidos.modelo_versao`, `apelidos.produto_nome`
- [X] T012 `src/pedido/store.py`: the modelos methods, `set_estado(..., modelo_versao=None)`, `produto_nome` in `upsert_positivo`/`list_apelidos`, `sincronizar_apelidos`
- [X] T013 `src/pedido/modelos.py`: `ModeloService`, `ModeloAtivo`, `ModeloIndisponivel`, comparison of two catalogs
- [X] T014 **Confirm GREEN**: T004–T008 pass; the whole 004 suite still passes

**Checkpoint**: models are stored, validated, activated and compared, with no HTTP yet.

---

## Phase 3: User Story 1 - Export the model (Priority: P1)

### Tests (write first)

- [X] T015 [P] [US1] Write `tests/contract/test_api_modelo.py` (export part): `GET /api/modelo` returns the seed as an attachment named `modelo-pedido.xlsx`, a real `.xlsx` with 167 products and 189 formulas; after an import it returns the new model
- [X] T016 [US1] **Confirm RED**

### Implementation

- [X] T017 [US1] `src/pedido/web/app.py`: build the `ModeloService` (seed at startup, nickname names filled), give the `Conversa` the service, add `GET /api/modelo`
- [X] T018 [US1] **Confirm GREEN**

---

## Phase 4: User Story 2 - Import a new model (Priority: P1)

### Tests (write first)

- [X] T019 [P] [US2] Extend `tests/contract/test_api_modelo.py`: `POST /api/modelo` with the model plus a new product answers the summary (`adicionados`, version 2); the next order naming the product gets it and the confirmed Excel has the quantity in its cell, with no restart; the unchanged export imported again reports nothing added, removed or renamed; renamed and removed products are listed; `.xls`, empty, garbage, no products, repeated name, merged cell → `422 modelo_invalido` with the message of the contract and the active model unchanged (`GET /api/modelo/info` and the next order prove it); too large → `413 modelo_grande`; the file name header is stored; every previous model is still in the table
- [X] T020 [US2] **Confirm RED**

### Implementation

- [X] T021 [US2] `src/pedido/web/app.py`: `POST /api/modelo` (raw body, size check before reading everything it can, `X-Nome-Arquivo`, errors `modelo_invalido`/`modelo_grande` with the specific message)
- [X] T022 [US2] **Confirm GREEN**

---

## Phase 5: User Story 3 - The customer is told to check the model (Priority: P1)

### Tests (write first)

- [X] T023 [P] [US3] Write `tests/unit/test_conversa_modelo.py`: a catalog list still works as a static model; with the service, an order after an import naming the new product lists it; when the model cannot be read or has no products an order gets `MODELO_INVALIDO`, nothing is stored and a pending order is kept; `ok` after a new model that lacks a product of the pending order (or has another name at its position) gets `MODELO_PRODUTO_AUSENTE`, no file, order still pending, and a new order replaces it and works; `ok` after a new model that keeps all products sends the Excel filled with the NEW model; the confirmed order records its model version and `GET /api/pedidos/{id}/planilha` regenerates it from that version even after another import; replies for normal orders are byte-identical to 004
- [X] T024 [US3] **Confirm RED**

### Implementation

- [X] T025 [US3] `src/pedido/conversa.py`: accept a model provider (a list becomes a static one), cache the matcher and chains per version, the two replies, the product check at `ok`, record the version at confirmation; `src/pedido/web/app.py`: the planilha download uses the order's version
- [X] T026 [US3] **Confirm GREEN**: the whole suite passes

---

## Phase 6: User Story 4 - Information about the active model (Priority: P2)

- [X] T027 [P] [US4] Extend `tests/contract/test_api_modelo.py`: `GET /api/modelo/info` returns version 1, the seed file name, 167 products and an ISO time; after an import it shows version 2, the file name and the new count
- [X] T028 [US4] **Confirm RED**, then add `GET /api/modelo/info` to `src/pedido/web/app.py` and **confirm GREEN**

---

## Phase 7: User Story 5 - Nicknames follow the model (Priority: P2)

- [X] T029 [P] [US5] Write `tests/unit/test_apelidos_modelo.py` (through the service and the app): a nickname learned records the product name (`aprender` receives the names); an import that removes or renames its product disables it and still lists it; an unchanged model keeps it active; exporting and importing the same file keeps every nickname active; old nicknames without a name are filled at startup; the import summary reports the number disabled
- [X] T030 [US5] **Confirm RED**, then pass the names in `src/pedido/memoria.py`/`src/pedido/conversa.py`, call the synchronization at startup and on every activation, and **confirm GREEN**

---

## Phase 8: Polish & Cross-Cutting Concerns

- [X] T031 [P] Update `scripts/apelidos.py` to show the stored product name and a note when the product changed; add a case to `tests/unit/test_script_apelidos.py`
- [X] T032 [P] Add `MAX_MODELO_MB` to `.env.example`; add an update note to `specs/004-memoria-e-guardrails/spec.md`
- [X] T033 [P] Re-run `tests/unit/test_ptbr_strings.py` with all the new texts
- [X] T034 Full validation: `uv run pytest`; the quickstart 2–8 on the real app with Ollama; record the results in `research.md`
- [X] T035 [P] Final cleanup: no file content or phone number in logs; no key in any file

---

## Dependencies & Execution Order

- **Setup (1)** → **Foundational (2)** → stories. **US1** and **US2** need the service; **US3** needs US2; **US4** needs US2; **US5** needs US2.
- Within a phase: tests → **Confirm RED** → implementation → **Confirm GREEN**.

## Implementation Strategy

1. MVP = Foundational + US1 + US2 + US3: export, import and the model-problem replies.
2. Then US4 (information) and US5 (nicknames follow the model), then Polish.
3. The stock-system screen is a separate feature in the other repository and starts after T034.
