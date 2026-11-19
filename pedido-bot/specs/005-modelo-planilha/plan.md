# Implementation Plan: Modelo de planilha gerenciado

**Branch**: `005-modelo-planilha` (no git repository; folder name only) | **Date**: 2026-11-18 | **Spec**: [spec.md](spec.md)

**Input**: Feature specification from `/specs/005-modelo-planilha/spec.md`

## Summary

The order-form model stops being a fixed file. Models live in Postgres with versions (one active, none ever
deleted); the repository file is only the seed. A `ModeloService` validates an uploaded `.xlsx`, activates it,
rebuilds the catalog from it without a restart and reports what was added, removed or renamed. The
conversation reads the catalog of the **active** model on every message and answers one neutral sentence
about checking the model when the model cannot be used or a product of a pending order left it. Learned
nicknames remember the product name and are disabled when their product disappears or is renamed. Three API
routes: download the model, upload a model, information. A confirmed order remembers the model version it
was filled with, so its Excel can always be regenerated. See [research.md](research.md).

## Technical Context

**Language/Version**: Python 3.11 (`uv`, as before)

**Primary Dependencies**: unchanged (FastAPI, openpyxl, psycopg, pgvector, LangChain, rapidfuzz). No new
dependency: the upload is the raw request body (no multipart).

**Storage**: Postgres 16 + pgvector; new table `modelos`; new columns `pedidos.modelo_versao` and
`apelidos.produto_nome`.

**Testing**: pytest on real Postgres; xlsx fixtures built with openpyxl from the seed (add a product, rename,
remove, merge a cell, duplicate a name); no network.

**Performance Goals**: each model request under 3 s for 200 products; the catalog is rebuilt only when the
active version changes (one cheap query per message to see the version).

**Constraints**: replies for normal orders byte-identical to 004; an invalid import never changes anything;
nothing is deleted; limit 5 MB (`MAX_MODELO_MB`).

## Constitution Check

*GATE: passed before Phase 0; re-checked after Phase 1.* Constitution **v2.2.0**.

| Principle / constraint | Gate | Status |
|---|---|---|
| I. pt-BR everywhere | new replies, API errors and summaries are constants of `messages.py`; scanner test covers them | PASS |
| II. Test-First | tests first for validation, service, store, conversation, API; real Postgres; xlsx built in tests | PASS (tasks ordering) |
| III. The Customer Confirms | model problems = one neutral sentence about checking the model, pending order kept; no file; closest-match untouched | PASS |
| IV. Closest Match, Exact First | catalog derived from the active model; nicknames store the name and are disabled on change | PASS |
| V. Deterministic Core | validation, comparison and synchronization are plain Python; no model involved | PASS |
| VI. Orders Are Persisted | models stored with versions (never deleted); a confirmed order records its model version | PASS |
| VII. Scope | API only (download, upload, info); no screen, no restore endpoint, no keys, no WhatsApp | PASS |
| VIII. Guardrails | size limit and validation guard the upload; logs never hold file content | PASS |
| Tech: template rules, validation list, 5 MB | see research D2, D3 | PASS |

Post-design re-check: **PASS**, no violations.

## Project Structure

### Documentation (this feature)

```text
specs/005-modelo-planilha/
├── plan.md  research.md  data-model.md  quickstart.md
├── contracts/ (http-api.md, replies.md)
├── checklists/requirements.md
└── tasks.md            # /speckit-tasks output (NOT created here)
```

### Source Code (repository root)

```text
src/pedido/
├── config.py       # + MAX_MODELO_MB (default 5)
├── messages.py     # + MODELO_* replies, API errors for the model, summary labels
├── catalog.py      # load_catalog accepts bytes; validar_modelo(bytes) -> catalog or ModeloInvalido
├── export.py       # fill_template accepts bytes; quantities_for_export refuses unknown products
├── modelos.py      # NEW: ModeloService (seed, atual, por_versao, importar, comparar), ModeloIndisponivel
├── schema.sql db.py# table modelos; pedidos.modelo_versao; apelidos.produto_nome
├── store.py        # modelos CRUD; apelidos names + sincronizar; set_estado records the version
├── chains.py       # build_export_chain(catalog, template) with bytes
├── conversa.py     # takes a model provider (a plain catalog list still works); model-problem replies
├── memoria.py      # aprender receives the product names
└── web/app.py      # GET/POST /api/modelo, GET /api/modelo/info; download uses the order's model version
tests/              # new unit/contract tests; helpers to build model variants
```

**Structure Decision**: one new module (`modelos.py`) owns "which model is active"; the engine and the app
ask it for the current catalog, matcher inputs and template bytes. Everything else reuses 003/004.

## Complexity Tracking

No constitution violations to justify.
