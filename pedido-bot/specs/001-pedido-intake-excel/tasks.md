---
description: "Task list for Pedido a partir de mensagem de WhatsApp (intake → Excel)"
---

# Tasks: Pedido a partir de mensagem de WhatsApp (intake → Excel)

**Input**: Design documents from `/specs/001-pedido-intake-excel/`

**Prerequisites**: plan.md, spec.md, research.md, data-model.md, contracts/http-api.md, quickstart.md

**Tests**: **REQUIRED** (Constitution Principle II, Test-First, NON-NEGOTIABLE). In every phase, test
tasks come first, and a "confirm RED" task proves they fail for the right reason *before* any
implementation task. Never write implementation to make an unwritten test pass.

**Organization**: grouped by user story. **Phase order note:** US3 (strict matching) is built
*before* US1 because US1's proposal consumes the matcher; all three of US1/US2/US3 are P1.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: can run in parallel (different files, no dependency on an incomplete task)
- **[Story]**: US1–US5 from spec.md (none in Setup, Foundational, Polish)
- All user-facing strings, prompts, flags and error messages are **pt-BR** (Constitution I)

## Path Conventions

Single project: `src/pedido/`, `tests/`, `assets/`, `data/` at the repository root
(`/Users/gabrielmnoma/Coding/tests/project-R`), per plan.md.

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: project skeleton, dependencies, and the template files in place

- [X] T001 Create the directory skeleton from plan.md: `src/pedido/web/templates/`, `src/pedido/web/static/`, `tests/unit/`, `tests/contract/`, `tests/integration/`, `tests/fixtures/mensagens/`, `tests/fixtures/llm_stubs/`, `assets/original/`, `data/`, `scripts/`, plus empty `src/pedido/__init__.py` and `src/pedido/web/__init__.py`
- [X] T002 Create `pyproject.toml` (Python 3.11; deps: fastapi, uvicorn, jinja2, langchain-core, langchain-anthropic, rapidfuzz, openpyxl; dev: pytest, httpx; pytest `testpaths = ["tests"]`, `pythonpath = ["src"]`) and run `uv sync` to create the lock file
- [X] T003 [P] Copy (do not move) `/Users/gabrielmnoma/Downloads/PLANILHA-2024.xlsx` to `assets/PLANILHA_2024.xlsx`
- [X] T004 [P] Copy `/Users/gabrielmnoma/Downloads/PLANILHA 2024.xls` to `assets/original/PLANILHA 2024.xls` and make it read-only (`chmod a-w`); it is never modified (FR-012)

**Checkpoint**: `uv run pytest` runs (collects zero tests) with no import errors.

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: normalizer, catalog loader, store, config, plus the shared fixtures and the regression
message set. **No user story work starts until this phase is green.**

### Tests first (write all, then confirm they fail)

- [X] T005 [P] Write shared fixtures in `tests/conftest.py`: temporary SQLite path, loaded catalog from `assets/PLANILHA_2024.xlsx`, a factory for a stub chat model that returns canned structured responses from `tests/fixtures/llm_stubs/`, and a FastAPI `TestClient` fixture (app import deferred until it exists)
- [X] T006 [P] Generate candidate abbreviations from the catalog names (tokens ending in `.`, truncated words) with a one-off script in `scripts/derive_abbreviations.py`, write `assets/abbreviations.json`, then **ask the user to review it**; T012 and T016 must not start until it is reviewed (spec: "list derived from the catalog and reviewed by the user")
- [X] T007 [P] Write `tests/unit/test_catalog.py` against `assets/PLANILHA_2024.xlsx`: exactly 167 products (the 178 non-empty name-column cells minus 11 footer formulas); no catalog name starts with `=`; "Abre Caminho" is block 1, row 4, `celula_qtd == "A4"`; blocks 1–3 → `Defumadores`, blocks 4–5 → `Incensos`; `nome_normalizado` unique; **no `celula_qtd` is a merged cell**; every quantity cell sits two columns left of its name cell; the header **input** cells `Q1`, `D2`, `I2`, `D3`, `I3`, `M3`, `Q3` are empty in the template and the labels `P1`, `A2`, `H2`, `A3`, `H3`, `K3`, `P3` hold the expected text
- [X] T008 [P] Write `tests/unit/test_store.py`: schema creation; alias upsert where the latest confirmation wins; `run_lines` keeps `produto_sugerido`/`confianca` next to `produto_final`/`qtd_final`; an `aprovado` run rejects edits; removed lines are kept with null finals (data-model.md)
- [X] T009 [P] Author the regression set in `tests/fixtures/mensagens/` (~20 synthetic pt-BR messages as `*.txt` plus one `expected.json` with, per line: written text, quantity in dozens, expected product name or `null`, expected `motivo`/flags). Must include: abbreviations ("abre c. da felicidade", "def. do preto velho"), "meia dúzia", several items per message, typos **inside the "Abre …" family**, a product not in the catalog, a non-dozen unit, a duplicate product, a message with no order at all, mixed case and missing accents. **Written before any match/extract code.** The set is synthetic: extend or replace it with real customer messages as soon as the user has some (SC-001 is only meaningful with real wording)
- [X] T010 [P] Author canned LLM responses in `tests/fixtures/llm_stubs/` (extract output per fixture message; tie-break answers incl. one that returns an id outside the candidates and one `null`)
- [X] T011 [P] Write `tests/unit/test_ptbr_strings.py` (Constitution I enforced test-first): a scanner that fails on non-pt-BR user-facing text in `src/pedido/messages.py` (the single module holding every user-visible string, flag label and API error `mensagem`), `src/pedido/web/templates/` and `src/pedido/web/static/`; a string passes only if it contains pt-BR content (accents or common pt-BR words) and none of a banned-English list ("Error", "Submit", "Loading", "Approve", …); it must pass on empty directories and pick up new files automatically
- [X] T012 Write `tests/unit/test_normalize.py` (needs the reviewed `assets/abbreviations.json` from T006): lowercase; strip accents; `.` replaced by space ("Nossa Sra.Des.dos Nos" → tokens split); collapsed spaces; abbreviation expansion (`c`→`caminho`, `def`→`defumador`); **"Abre C. da Felicidade" and "abre caminho da felicidade" normalize identically**; "abre caminho" ≠ "abre caminho da felicidade"
- [X] T013 **Confirm RED**: run `uv run pytest tests/unit/test_normalize.py tests/unit/test_catalog.py tests/unit/test_store.py tests/unit/test_ptbr_strings.py` and confirm every test fails because the modules do not exist yet (not because of a typo in the tests); note the result in the task

### Implementation

- [X] T014 Implement `src/pedido/config.py`: thresholds (`FUZZY_MIN_SCORE=95`, `FUZZY_MIN_LEAD=10`, `SIBLING_WINDOW=15`, `LOW_CONFIDENCE=0.90`), model name, `ANTHROPIC_API_KEY` read from the environment only, paths to the template, abbreviations file and SQLite file
- [X] T015 Create `src/pedido/messages.py`: the single source of every user-visible pt-BR string (flag labels `revisar`, `sem_produto`, `baixa_confianca`, …; the API error `mensagem` texts from contracts/http-api.md; the "nada reconhecido" `aviso`), so routes, validators and templates import from it and never hard-code text; makes `tests/unit/test_ptbr_strings.py` pass
- [X] T016 Implement `src/pedido/normalize.py` (lowercase, accent strip, `.`→space, collapse, abbreviation expansion) to make `tests/unit/test_normalize.py` pass
- [X] T017 Implement `src/pedido/catalog.py`: read `assets/PLANILHA_2024.xlsx` with `openpyxl`, scan name columns C, G, K, O, S rows 4–46 skipping any cell whose text starts with `=` (footer formulas), derive category from block, compute `celula_qtd`, build normalized names, and fail loudly on duplicate normalized names, to make `tests/unit/test_catalog.py` pass (catalog names are matched exactly by `match`; they are **not** seeded as aliases)
- [X] T018 Implement `src/pedido/store.py` (stdlib `sqlite3`; tables `catalog`, `aliases`, `runs`, `run_lines` exactly as in data-model.md; create-on-startup) to make `tests/unit/test_store.py` pass
- [X] T019 **Confirm GREEN**: `uv run pytest tests/unit/test_normalize.py tests/unit/test_catalog.py tests/unit/test_store.py tests/unit/test_ptbr_strings.py` all pass

**Checkpoint**: foundation ready; catalog loads 167 products with correct cells and categories.

---

## Phase 3: User Story 3 - Never confuse similar products (Priority: P1) 🎯

**Goal**: the strict matching engine (Constitution IV). Built first because US1 consumes it.

**Independent Test**: run the regression set's lines through the matcher with a stubbed tie-break:
exact names resolve correctly, in-family typos are flagged, and **zero** lines are auto-accepted to a
wrong product.

### Tests for User Story 3 (write first)

- [X] T020 [P] [US3] Write `tests/unit/test_match.py`: exact normalized match auto-accepts (`motivo=exato`, `confianca=1.0`); alias match auto-accepts (`motivo=alias`, `confianca=1.0`); **"abre caminho" → Abre Caminho, "abre c. da felicidade" → Abre C. da Felicidade, never the other**; "abre caminho" never resolves to "Abre Caminho da Felicidade"; "abre camino" (typo in the "Abre …" family) is flagged `revisar` with ≤ 3 candidates, `precisa_revisao=true`, and **not** auto-accepted (sibling guard); a typo of a product whose first word is unique in the catalog, with score ≥ 95 and lead ≥ 10 (e.g. "descarrego completto"), is auto-accepted (`fuzzy_seguro`, `confianca = score/100`); a typo of a product in a first-word family ("Abre …", "Quebra …", "Chama …", "Sete …") is **never** auto-accepted, even at score ≥ 95; score 94 or lead 9 is flagged; the tie-break may only pre-select among the given candidate ids, ignores ids outside them, treats `null` as no preselection, and **never** sets auto-accept; thresholds are read from `config.py`
- [X] T021 [P] [US3] Write `tests/unit/test_match_regression.py`: for every line in `tests/fixtures/mensagens/expected.json`, run `match_one` and assert (a) zero auto-accepted lines are wrong, (b) every line expected as `revisar`/`sem_correspondencia` is flagged, (c) unmatched products are flagged, never dropped
- [X] T022 [US3] **Confirm RED**: run `uv run pytest tests/unit/test_match.py tests/unit/test_match_regression.py`; confirm they fail only because `pedido.match` is missing

### Implementation for User Story 3

- [X] T023 [US3] Implement the core of `src/pedido/match.py`: normalize query and catalog, exact/alias auto-accept, `rapidfuzz` `token_sort_ratio` scoring over all products, safe-fuzzy rule (≥ `FUZZY_MIN_SCORE`, lead ≥ `FUZZY_MIN_LEAD`, sibling guard within `SIBLING_WINDOW` sharing the first word), top-3 `candidatos`, `motivo` codes from data-model.md
- [X] T024 [US3] Add to `src/pedido/match.py`: `tie_break` (injected chat model; pt-BR prompt; structured output `{produto_id | null}` restricted to candidate ids; result only sets a pre-selection) and `match_all` as `RunnableLambda(match_one).map()` so lines run in parallel
- [X] T025 [US3] **Confirm GREEN**: both US3 test files pass; the regression test reports zero wrong auto-accepts

**Checkpoint**: the matcher is independently correct and safe. US3 is done.

---

## Phase 4: User Story 1 - Turn a pasted message into a reviewed order (Priority: P1) 🎯 MVP

**Goal**: paste → proposed editable table → edit → approve, with all flags and blocking rules.

**Independent Test**: paste a multi-item message (LLM stubbed) and verify the table, flags, totals,
editing, blocked approval while lines are unresolved, and successful approval.

### Tests for User Story 1 (write first)

- [X] T026 [P] [US1] Write `tests/unit/test_extract.py` (stub chat model): returns `[{texto, quantidade, unidade}]`; "meia dúzia" → 0.5; "2 dz" → 2; a message with no order returns an empty list (not an error); the prompt text is pt-BR; the model is injected, never constructed inside the function
- [X] T027 [P] [US1] Write `tests/unit/test_validate.py`: flags `sem_produto`, `baixa_confianca` (confianca below `LOW_CONFIDENCE`), `quantidade_invalida` (≤ 0 or not a multiple of 0.5), `unidade_nao_duzia`, `duplicado`; no line is dropped; totals per category (`Defumadores`, `Incensos`, `Def/Inc`) computed from the lines; flag labels are pt-BR; an `unresolved(lines)` helper treats as unresolved: no product, invalid quantity, a `duplicado` pair, and any `precisa_revisao` line without `confirmado`
- [X] T028 [P] [US1] Write `tests/contract/test_api_proposta.py` per contracts/http-api.md: `POST /api/pedidos` 200 shape (`linhas`, `totais`, `candidatos`, `flags`, `precisa_revisao`), empty `linhas` plus pt-BR `aviso` when nothing is recognized, 400 `mensagem_vazia`; `GET /api/catalogo?q=` accent/case-insensitive, max 20; `POST /api/pedidos/{id}/aprovar` → **409 `linhas_pendentes` (with the pending ids and no state change) for each of: no product, invalid quantity, duplicate product, and a `precisa_revisao` line without `confirmado: true`**; 200 on a clean table; a payload where the user merged two duplicate lines into one (quantities added) is accepted; `confirmado` is required only for `precisa_revisao` lines; 404 `pedido_nao_encontrado`; **every error `mensagem` is pt-BR**
- [X] T029 [P] [US1] Write `tests/integration/test_proposal_chain.py`: `extract | match_all | validate` end to end with stubs over the regression messages; asserts line count, flags, and totals
- [X] T030 [US1] **Confirm RED**: run the four US1 test files; confirm they fail only because `extract`, `validate`, `chains` and the app do not exist

### Implementation for User Story 1

- [X] T031 [P] [US1] Implement `src/pedido/extract.py`: pt-BR prompt, `ChatAnthropic.with_structured_output` schema `[{texto, quantidade, unidade}]`, model injected
- [X] T032 [P] [US1] Implement `src/pedido/validate.py`: flag rules and category totals from data-model.md
- [X] T033 [US1] Implement the proposal chain in `src/pedido/chains.py`: `RunnableLambda(extract) | match_all | RunnableLambda(validate)`, persisting each stage's suggestion, `confianca` and `precisa_revisao` into `run_lines` through `store.py`
- [X] T034 [US1] Implement `src/pedido/web/app.py`: app factory, a single pt-BR error handler producing `{erro, mensagem}`, `POST /api/pedidos`, `GET /api/catalogo`
- [X] T035 [US1] Add `POST /api/pedidos/{id}/aprovar` to `src/pedido/web/app.py` and the approval state transition to `src/pedido/store.py`: re-check on the server using `validate.unresolved` and reject with 409 `linhas_pendentes` while any line has no product, an invalid quantity, a duplicate product, or `precisa_revisao` without `confirmado`; accept `id: null` lines as user-added; omitted lines are treated as removed; store `confirmado` per line (required only for `precisa_revisao` lines)
- [X] T036 [US1] Build the pt-BR page: `src/pedido/web/templates/index.html`, `src/pedido/web/static/app.js`, `src/pedido/web/static/app.css`: paste box and "Analisar" button; editable table (product via searchable dropdown, quantity, remove, add line); "revisar" highlighting with up to 3 candidates and an explicit "Confirmar" action per flagged line (a suggestion is never accepted by default); a client-side "Mesclar" action for duplicate products (the page sends one merged line with the quantities added; the server never merges); `confirmado: true` is sent only for lines the user confirmed or edited; the "nada reconhecido" note when `aviso` is present; per-category totals; "Aprovar" disabled while lines are unresolved
- [X] T037 [US1] **Confirm GREEN**: US1 tests pass; quickstart scenarios 1 and 4 were driven in a real browser with a stubbed LLM (no API key available); the same scenarios with the real API are repeated in T062

**Checkpoint**: a user can paste, review, correct and approve an order. MVP of the review loop.

---

## Phase 5: User Story 2 - Get the filled order form (Priority: P1) 🎯

**Goal**: approved quantities written into the right cells of the `.xlsx` copy, formulas intact.

**Independent Test**: approve a known order, download the file, and verify quantities per product
cell, header blank, formulas unchanged, original `.xls` untouched.

### Tests for User Story 2 (write first)

- [X] T038 [P] [US2] Write `tests/unit/test_export.py`: each approved quantity lands in the product's `celula_qtd`; **all 189 formulas are still present and unchanged** after a fill; header input cells `Q1`, `D2`, `I2`, `D3`, `I3`, `M3`, `Q3` stay empty **and the labels** (`P1`, `A2`, `H2`, `A3`, `H3`, `K3`, `P3`) **stay unchanged**; no write targets a merged cell; `fullCalcOnLoad` is set; the app's category totals equal the sum of the quantity cells in the filled file; the source template and `assets/original/PLANILHA 2024.xls` are byte-for-byte unchanged
- [X] T039 [P] [US2] Write `tests/contract/test_api_planilha.py`: `GET /api/pedidos/{id}/planilha` → 200 `.xlsx` attachment named `pedido-{id}.xlsx` for an approved run; **409 `pedido_nao_aprovado`** for a `proposto` run; pt-BR messages
- [X] T040 [US2] **Confirm RED**: run both US2 test files; confirm they fail only because `export` and the route do not exist

### Implementation for User Story 2

- [X] T041 [US2] Implement `src/pedido/export.py`: load the `.xlsx` copy with `openpyxl` (formulas kept), write only quantity cells from `catalog.celula_qtd`, set `fullCalcOnLoad`, return bytes from a temporary copy (never write over the template)
- [X] T042 [US2] Add the fill step (`RunnableLambda(fill_template)`, invoked at download, separate from the approval step) in `src/pedido/chains.py` and the `GET /api/pedidos/{id}/planilha` route in `src/pedido/web/app.py`, refusing unapproved runs
- [X] T043 [US2] Add the "Baixar planilha" button, shown only after approval, to `src/pedido/web/templates/index.html` and `src/pedido/web/static/app.js`
- [X] T044 [US2] **Confirm GREEN**: US2 tests pass (cell mapping, 189 formulas, header, merged cells, totals read back from the file); opening the downloaded file in Excel to see computed values and totals is checked in T062

**Checkpoint**: paste → review → approve → filled `.xlsx`. The three P1 stories are complete.

---

## Phase 6: User Story 4 - The system remembers my corrections (Priority: P2)

**Goal**: confirmed/corrected phrases become aliases; history shows suggestion vs final.

**Independent Test**: correct a line, approve, then paste the same wording and verify it matches
without review; open the history and see suggestion and final side by side.

### Tests for User Story 4 (write first)

- [X] T045 [P] [US4] Write `tests/unit/test_alias_learning.py`: approving a line the user confirmed or changed writes a normalized alias (`origem='correcao'`); an auto-accepted line (`precisa_revisao=false`) whose product the user did not change writes **no** alias, even if sent with `confirmado: true`; a line added by the user (empty `texto`) writes **no** alias; the next `match_one` for that wording returns `motivo=alias` without `revisar`; remapping the same phrase updates the alias (latest wins)
- [X] T046 [P] [US4] Write `tests/contract/test_api_historico.py`: `GET /api/pedidos` summaries; `GET /api/pedidos/{id}` returns each line's `produto_sugerido`, `confianca`, `produto_final`, `qtd_final` together; a second proposal for the same phrase shows `motivo: "alias"`
- [X] T047 [US4] **Confirm RED**: run both US4 test files; confirm they fail for the right reason

### Implementation for User Story 4

- [X] T048 [US4] Implement `save_corrections` as a `RunnableLambda` in `src/pedido/chains.py` (alias upsert for every `precisa_revisao` line the user confirmed and every line whose product the user changed, skipping lines with an empty `texto`; invoked at approval, before download) and run it inside the approval flow in `src/pedido/web/app.py`
- [X] T049 [US4] Add `GET /api/pedidos` and `GET /api/pedidos/{id}` to `src/pedido/web/app.py` with queries in `src/pedido/store.py`
- [X] T050 [US4] Add the history list and a side-by-side detail view (suggestion | final) to `src/pedido/web/templates/index.html` and `src/pedido/web/static/app.js`
- [X] T051 [US4] **Confirm GREEN**: US4 tests pass; run quickstart scenarios 6 and 8

**Checkpoint**: review effort shrinks over time and the data for the learning sub-project is being stored.

---

## Phase 7: User Story 5 - Failures never lose my work (Priority: P2)

**Goal**: LLM or export failures keep the user's text and approved order.

**Independent Test**: stub a failing extraction and a failing export; verify pt-BR messages, kept
text, retry, empty manual table, and a re-exportable approved run.

### Tests for User Story 5 (write first)

- [X] T052 [P] [US5] Write `tests/contract/test_api_falhas.py`: a failing extraction returns **502 `analise_indisponivel`** with the run `id`, empty `linhas`, and the stored message intact; a failing export returns **500 `falha_planilha`** and the run stays `aprovado` and exportable; all `mensagem` fields are pt-BR
- [X] T053 [P] [US5] Write `tests/unit/test_extract_fallback.py`: malformed structured output triggers exactly one retry; a second failure raises `ExtractionFailed` after exactly two attempts (the API turns it into a 502 with an empty table, never an error shown to the user)
- [X] T054 [US5] **Confirm RED**: run both US5 test files; confirm they fail for the right reason

### Implementation for User Story 5

- [X] T055 [US5] Add one retry and the empty-lines fallback to `src/pedido/extract.py`, and make `POST /api/pedidos` in `src/pedido/web/app.py` persist the run first and return 502 with the `id` on failure
- [X] T056 [US5] Wrap the fill step so failures return 500 `falha_planilha` without changing the run, in `src/pedido/export.py` and `src/pedido/web/app.py`
- [X] T057 [US5] In `src/pedido/web/static/app.js` and `index.html`: show the pt-BR failure message, keep the pasted text, offer "Tentar novamente" and an empty editable table for manual entry
- [X] T058 [US5] **Confirm GREEN**: US5 tests pass; run quickstart scenario 7

**Checkpoint**: all five stories work independently.

---

## Phase 8: Polish & Cross-Cutting Concerns

- [X] T059 [P] Re-run `tests/unit/test_ptbr_strings.py` now that the templates, static files and all API error/flag messages exist, and fix any non-pt-BR user-facing text it finds (the test itself was written first, in Phase 2; Constitution I and II)
- [X] T060 [P] Write `scripts/run_regression_real.py`: runs `tests/fixtures/mensagens/` through the real Claude API (manual, needs `ANTHROPIC_API_KEY`) and prints per-line correctness, auto-accept errors and flags
- [X] T061 Tune the thresholds in `src/pedido/config.py` against the regression set so SC-001 (≥ 90% lines correct without edits) and SC-002 (zero wrong auto-accepts) hold; record the final values and the evidence in `specs/001-pedido-intake-excel/research.md`
- [ ] T062 Run the full validation: `uv run pytest tests/unit tests/contract tests/integration` all green; quickstart scenarios 1–8 pass; time the proposal step alone (plan goal under 10 s) and a ~10-item order end to end (SC-003 < 3 minutes); confirm SC-004 by comparing the on-screen totals with the sheet's own `K46`, `S37`, `S44` and `Q46` after opening the file in Excel **Status:** done — all 179 automated tests green; quickstart scenarios 1, 4, 5b, 6, 7 and 8 driven in a real browser with a stubbed LLM; the app's category totals equal what the sheet's own footer ranges compute (118 + 49 = 167 for all products at 1 dz); a 10-item order takes 5–30 ms without the LLM, 2 ms to approve, 26 ms to export. **Pending (needs the user):** (1) run `ANTHROPIC_API_KEY=... uv run python scripts/run_regression_real.py --real` and scenarios 1–3 against the real API (SC-001 with the real model, SC-003 timing); (2) open a downloaded `.xlsx` in Excel and confirm values, `K46`/`S37`/`S44`/`Q46` and that the price formulas recalculate (SC-004).

---

## Dependencies & Execution Order

### Phase dependencies

- **Setup (1)** → **Foundational (2)** → everything else.
- **US3 (3)** needs Foundational. **US1 (4)** needs US3 (it calls `match_all`).
- **US2 (5)** needs US1's approval flow (T035) and the catalog's `celula_qtd` (T017).
- **US4 (6)** needs US1 (approval) and US3 (alias path in the matcher).
- **US5 (7)** needs US1 and US2 (it hardens both).
- **Polish (8)** needs all stories you intend to ship.

### Within every phase

Test tasks → **Confirm RED** → implementation → **Confirm GREEN**. Models/store before services,
services before endpoints, endpoints before UI.

### Parallel opportunities

- Setup: T003, T004 together.
- Foundational: T006 (abbreviations, needs your review) comes before T012 and T016; T005, T007–T011 can run together (different files; T011 is the pt-BR test).
- US3 tests: T020, T021 together. US1 tests: T026–T029 together; US1 impl: T031, T032 together.
- US2 tests: T038, T039. US4 tests: T045, T046. US5 tests: T052, T053. Polish: T059, T060.

---

## Implementation Strategy

1. **First usable version = US3 + US1 + US2** (the three P1 stories): matcher, review loop, filled form.
2. **Stop and validate after US1** (T037): you can already paste and review a table; show it to the user.
3. Add **US4** (learning data) and **US5** (resilience) next; they are P2 and do not change P1 behavior.
4. Finish with Polish; T061 is where the thresholds are tuned with evidence, not by hand per case.
