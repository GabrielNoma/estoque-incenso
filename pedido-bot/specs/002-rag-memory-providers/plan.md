# Implementation Plan: Banco único, serviços de IA configuráveis e memória de pedidos

**Branch**: `002-rag-memory-providers` (no git repository; folder name only) | **Date**: 2026-10-23 | **Spec**: [spec.md](spec.md)

**Input**: Feature specification from `/specs/002-rag-memory-providers/spec.md`

## Summary

Feature 001 keeps working unchanged for the user. Underneath: (1) **Postgres with pgvector becomes
the only database** (SQLite removed, schema `pedido`, `DATABASE_URL` required, the app refuses to
start in Portuguese without it); (2) **the LLM and the embedder are chosen by configuration**
(`anthropic` or any OpenAI-compatible service for the LLM; an OpenAI-compatible `/v1/embeddings`
service for vectors); (3) **a memory** is written at approval from confirmed data only (never blocking
an approval, with a reprocess command for pending vectors) and **read during the chain**: remembered
lines reorder and pre-select candidates for flagged lines (never auto-accept, with a family guard),
and similar past messages become few-shot examples for extraction. Technical approach in
[research.md](research.md): `psycopg` 3 + `pgvector`, `langchain-openai` for the OpenAI-compatible
adapters, cosine search with an HNSW index, a deterministic fake embedder and a fake OpenAI-compatible
server in tests, and a real pgvector Postgres in Docker for every database test.

## Technical Context

**Language/Version**: Python 3.11 (managed with `uv`, as in 001)

**Primary Dependencies**: adds `psycopg[binary]` (3.x), `pgvector` (Python adapter), `langchain-openai`
(chat + embeddings against OpenAI-compatible services); keeps FastAPI, Uvicorn, Jinja2,
`langchain-core`, `langchain-anthropic`, `rapidfuzz`, `openpyxl`. Removes the stdlib `sqlite3` Store.

**Storage**: Postgres 16 + pgvector, schema `pedido`. Local: `docker compose` (`pgvector/pgvector:pg16`).
Hosted later (Supabase): change `DATABASE_URL` only.

**Testing**: pytest. Database tests run against the real Postgres (Docker). A deterministic
`FakeEmbedder` and a fake OpenAI-compatible HTTP server (a small FastAPI app on a random local port)
keep every test off the internet. The 179 tests of 001 are migrated to the new `Store`, not dropped.

**Target Platform**: the user's own computer (macOS); hosted Postgres later.

**Project Type**: web-service (single project), unchanged from 001.

**Performance Goals**: memory help adds at most `EMBED_TIMEOUT_SECONDS` (5 s) to a proposal and is
skipped when slower; embeddings are batched (one call for the message plus the flagged lines); an
approval never waits for the embedder beyond that limit; nearest-neighbor queries answer in tens of
milliseconds at this scale.

**Constraints**: all user-facing text pt-BR; keys only from the environment, never stored or shown;
approval succeeds even if embedding fails; memory help never auto-accepts and never weakens strict
matching; vector dimension fixed at table creation; no application data in local files.

**Scale/Scope**: one user, tens of orders per day → thousands of remembered lines per year; an exact
(unindexed) scan would suffice, the HNSW index is kept for the hosted future.

## Constitution Check

*GATE: passed before Phase 0 research; re-checked after Phase 1 design.* Constitution **v1.1.0**.

| Principle / constraint | Gate | Status |
|---|---|---|
| I. pt-BR everywhere | new reasons, statuses, startup errors and reprocess output go through `messages.py`; the scanner test covers them | PASS |
| II. Test-First | every module's tests come first (RED observed); DB tests on real Postgres; fake embedder and fake OpenAI-compatible server, no internet in tests | PASS (tasks ordering) |
| III. Human-in-the-loop | memory help only reorders/pre-selects; approval rules unchanged; flagged lines still need confirmation | PASS |
| IV. Strict matching | exact/alias/safe-fuzzy unchanged with the family guard; memory is advisory and has its own look-alike guard (research D5) | PASS |
| V. Deterministic core, models at the edges | LLM and embedder injected; retrieval ranking and the guard are pure functions; embedding batched | PASS |
| VI. Learning-ready data | memory written only at approval from final confirmed lines; failure leaves an empty-vector row; every row records the model | PASS |
| VII. Scope | RAG in scope; no WhatsApp, voice/image, header/client store, prices; no memory browser or deletion | PASS |
| Tech: Postgres only, `DATABASE_URL`, schema `pedido`, configurable providers, keys in env | see research D1–D4, data-model, contracts/configuration.md | PASS |

Post-design re-check (after Phase 1): **PASS**, no violations. Deliberate scope notes: no connection
pool (a connection per operation is enough for one user and works behind Supabase's pooler); no
migration framework (one idempotent `schema.sql`).

## Project Structure

### Documentation (this feature)

```text
specs/002-rag-memory-providers/
├── plan.md
├── research.md
├── data-model.md
├── quickstart.md
├── contracts/
│   ├── configuration.md     # environment variables, startup messages
│   ├── http-api-changes.md  # what changes in the 001 HTTP contract
│   └── reprocess-cli.md     # the memory reprocess command
├── checklists/requirements.md
└── tasks.md                 # /speckit-tasks output (NOT created here)
```

### Source Code (repository root)

```text
docker-compose.yml                 # NEW: db service (pgvector/pgvector:pg16), port 5433
.env.example                       # NEW: every variable, no secrets
src/pedido/
├── config.py                      # CHANGED: DATABASE_URL, LLM_*, EMBED_*, MEMORY_* thresholds; no SQLite path
├── messages.py                    # CHANGED: startup/DB errors, memory reasons and states in pt-BR
├── schema.sql                     # NEW: idempotent DDL for schema `pedido` (+ vector index)
├── db.py                          # NEW: connect(), apply_schema(), check_database(), StartupError
├── store.py                       # REWRITTEN for Postgres: same API + memory tables, memoria_estado
├── llm.py                         # NEW: build_chat_model(env) -> anthropic | openai_compatible
├── embeddings.py                  # NEW: Embedder protocol, OpenAICompatibleEmbedder, SafeEmbedder
├── memory.py                      # NEW: write at approval, neighbors, ranking merge, look-alike guard
├── reprocess.py                   # NEW: `python -m pedido.reprocess`
├── __main__.py                    # NEW: `python -m pedido` (validates config, then serves)
├── match.py                       # CHANGED: optional memory help (reorder + pre-select, never auto)
├── extract.py                     # CHANGED: optional few-shot examples in the prompt
├── chains.py                      # CHANGED: examples retrieval, batch embedding, save_memory step
└── web/app.py                     # CHANGED: create_app(database_url, chat_model, embedder), history memoria field
tests/
├── conftest.py                    # CHANGED: real-Postgres fixtures, FakeEmbedder, fake OpenAI server
├── fakes.py                       # NEW: FakeEmbedder (word-hash vectors), fake OpenAI-compatible app
├── unit/                          # + test_db, test_llm, test_embeddings, test_memory, test_reprocess,
│                                  #   test_match_memory, test_extract_examples; migrated test_store
├── contract/                      # + test_api_memoria; migrated 001 contract tests
└── integration/                   # + test_memory_flow (approve → remember → help next proposal)
```

**Structure Decision**: same single package as 001; new modules each have one responsibility and
are injected into `create_app`. No SQLite code remains.

## Complexity Tracking

No constitution violations to justify.
