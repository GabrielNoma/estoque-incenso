# Implementation Plan: Pedido a partir de mensagem de WhatsApp (intake → Excel)

> **Atualização (feature 002):** o armazenamento deste projeto mudou de SQLite para **Postgres com pgvector** (schema `pedido`, `DATABASE_URL` obrigatória). Onde este documento falar de SQLite ou `data/pedido.db`, vale o que está em `specs/002-rag-memory-providers/`. O restante continua válido.


**Branch**: `001-pedido-intake-excel` (no git repository; folder name only) | **Date**: 2026-10-23 | **Spec**: [spec.md](spec.md)

**Input**: Feature specification from `/specs/001-pedido-intake-excel/spec.md`

## Summary

A local, single-user web tool (pt-BR). The user pastes a customer's WhatsApp order text; a
LangChain LCEL chain **extracts** lines, **matches** each to the 167-product catalog (in parallel,
strict rules), and **validates**; the user reviews and edits an editable table and approves; a second
chain **saves corrections as aliases** and **fills the order form** (quantities only, at download); the two steps run at two endpoints, not
one pipe.
Technical approach, driven by [research.md](research.md): Python 3.11 + FastAPI + SQLite (stdlib),
`rapidfuzz` for candidate scoring, `openpyxl` to fill a one-time `.xlsx` copy of the form (its 189
formulas preserved), Claude via `langchain-anthropic` used only for extraction and ambiguous
tie-breaks.

## Technical Context

**Language/Version**: Python 3.11 (installed; managed with `uv`)

**Primary Dependencies**: FastAPI, Uvicorn, Jinja2, `langchain-core`, `langchain-anthropic`,
`rapidfuzz`, `openpyxl` (exact versions resolved and locked by `uv` at implementation time)

**Storage**: SQLite single file (`data/pedido.db`) via stdlib `sqlite3`; no ORM

**Testing**: pytest (+ FastAPI `TestClient`/`httpx`); LLM stages tested with stub Runnables; a
synthetic pt-BR regression set under `tests/fixtures/`

**Target Platform**: the user's own computer (macOS), run locally

**Project Type**: web-service (single project; server-rendered page + small JS, no build step)

**Performance Goals**: proposal for a ~10-item message in under 10 s end to end (dominated by one
LLM call); matching and validation under 100 ms; export under 1 s

**Constraints**: all user-facing text pt-BR; original `PLANILHA 2024.xls` never modified; filled
form keeps every formula; no network needed except the LLM calls; API key via environment only,
never written to the repo or database

**Scale/Scope**: one user, tens of orders per day, ~167 products, one template

## Constitution Check

*GATE: passed before Phase 0; re-checked after Phase 1 (below).*

| Principle | Gate | Status |
|---|---|---|
| I. pt-BR everywhere | UI, prompts, flags, errors, API error messages all pt-BR; a test scans templates/messages for non-pt-BR strings | PASS (planned in tasks) |
| II. Test-First | Every module has its test task before its implementation task; regression set authored before `match`/`extract` code | PASS (tasks ordering rule) |
| III. Human-in-the-loop | Export endpoint refuses unapproved runs; approval blocked while any line unresolved, including `revisar` lines the user has not explicitly confirmed and duplicate products; no line dropped | PASS (contract: 409s; `confirmado` field) |
| IV. Strict matching | Auto-accept only exact/alias or safe fuzzy (≥95, lead ≥10, sibling guard); LLM tie-break never auto-accepts; thresholds in config | PASS (research D4, data-model) |
| V. Deterministic core, LLM at edges | LLM only in `extract` and `tie_break`; all else plain functions in `RunnableLambda`; per-line `.map()` | PASS (research D3) |
| VI. Learning-ready data | `run_lines` stores suggestion + final side by side; confirmed matches → aliases | PASS (data-model) |
| VII. YAGNI/scope | No WhatsApp, voice/image, header/client store, prices, vector RAG; no ORM, no JS build | PASS |

Post-design re-check (after Phase 1): **PASS**, no violations. One deliberate scope note: the
form's *price formulas stay inside the file untouched* (we never read or write prices), which
respects Principle VII.

## Project Structure

### Documentation (this feature)

```text
specs/001-pedido-intake-excel/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── contracts/
│   └── http-api.md      # Phase 1 output (HTTP interface of the web tool)
├── checklists/
│   └── requirements.md
└── tasks.md             # Phase 2 output (/speckit-tasks - NOT created by /speckit-plan)
```

### Source Code (repository root)

```text
pyproject.toml
assets/
├── original/PLANILHA 2024.xls     # untouched source (read-only)
├── PLANILHA_2024.xlsx             # one-time "Salvar como .xlsx" copy made by the user (see research D1)
└── abbreviations.json             # reviewed list: "c" → "caminho", "def" → "defumador", ...
scripts/                           # one-off helpers: derive_abbreviations.py, run_regression_real.py
data/
└── pedido.db                      # created at first run
src/pedido/
├── config.py                      # thresholds, model name, paths (single source)
├── messages.py                    # every user-visible pt-BR string (flags, errors, notes) in one place
├── normalize.py                   # lowercase, strip accents/punctuation, expand abbreviations
├── catalog.py                     # load products + cell positions from the .xlsx; seed aliases
├── extract.py                     # LLM stage: message → raw lines (pt-BR prompt, structured output)
├── match.py                       # exact/alias → safe fuzzy → candidates; LLM tie-break (suggestion only)
├── validate.py                    # flags + total dozens per category
├── export.py                      # write quantities into the .xlsx copy, keep formulas
├── store.py                       # sqlite: runs, run_lines, aliases
├── chains.py                      # LCEL: proposal chain and export chain
└── web/
    ├── app.py                     # FastAPI routes (see contracts/http-api.md)
    ├── templates/index.html       # pt-BR page
    └── static/{app.js,app.css}
tests/
├── fixtures/
│   ├── mensagens/                 # ~20 synthetic pt-BR messages + expected lines (written first)
│   └── llm_stubs/                 # canned extract / tie-break responses
├── unit/                          # normalize, match, validate, catalog, export, store
├── contract/                      # HTTP API behavior + pt-BR error messages
└── integration/                   # full proposal → approve → export with stubbed LLM
```

**Structure Decision**: a single Python package under `src/pedido/` with one module per
responsibility in the design spec §4, plus `tests/` split by unit, contract and integration. No
separate frontend project: one server-rendered page with a little vanilla JS keeps Principle VII.

## Complexity Tracking

No constitution violations to justify.
