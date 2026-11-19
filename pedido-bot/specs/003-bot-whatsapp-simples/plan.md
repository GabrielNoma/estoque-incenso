# Implementation Plan: Bot de pedidos simples (estilo WhatsApp)

**Branch**: `003-bot-whatsapp-simples` (no git repository; folder name only) | **Date**: 2026-11-16 | **Spec**: [spec.md](spec.md)

**Input**: Feature specification from `/specs/003-bot-whatsapp-simples/spec.md`

## Summary

A channel-agnostic conversation engine plus a very simple test chat page. The customer's text goes
through one short chain: **extract** (the only LLM call: text and quantity in dozens) → **match** every
item to the **closest** catalog product (exact wording first, no floor, ties by Excel order) →
**aggregate** (sum by product) → **render** the plain list ending in `ok ou não?`. The customer answers
ok (the Excel is generated and sent), não (the order is discarded) or anything else (a new order that
replaces the pending one). Everything is stored per phone number in Postgres. This **replaces** the review
flow of 001/002: the review screen, candidate selection, merge, aliases, flags, the RAG memory, the
embeddings and the reprocess command are removed. Kept and reused: catalog, normalization (with
full-wording variants), Excel filling, LLM provider adapters, Postgres access. See
[research.md](research.md) for the decisions.

## Technical Context

**Language/Version**: Python 3.11 (managed with `uv`, as before)

**Primary Dependencies**: FastAPI, Uvicorn, Jinja2, `langchain-core`, `langchain-anthropic`,
`langchain-openai`, `rapidfuzz`, `openpyxl`, `psycopg[binary]`. **Removed**: `pgvector`.

**Storage**: Postgres 16 (schema `pedido`), pgvector NOT required. The `docker-compose.yml` image stays
(harmless); hosted Supabase later by changing `DATABASE_URL` only.

**Testing**: pytest on a real Postgres (Docker); an injected stub for the LLM and a fake
OpenAI-compatible server for the provider adapters; no test needs the internet.

**Target Platform**: the user's computer (macOS) for now; the chat page is served by the same app.

**Project Type**: web-service (single project).

**Performance Goals**: one reply per message; matching, summing and rendering under 50 ms; the reply
time is dominated by the single LLM call (seconds with a local 14B model).

**Constraints**: all customer-facing text pt-BR; the reply to an order is exactly the list plus the
closing line; no file before ok; keys only from the environment; no data in local files.

**Scale/Scope**: one business, tens of conversations a day, 167 products, one template.

## Constitution Check

*GATE: passed before Phase 0; re-checked after Phase 1.* Constitution **v2.0.0**.

| Principle / constraint | Gate | Status |
|---|---|---|
| I. pt-BR everywhere | every reply and the chat page text live in `messages.py`; the scanner test covers them | PASS |
| II. Test-First | each module's tests come first (RED observed); real Postgres; stub LLM; fake OpenAI server | PASS (tasks ordering) |
| III. The Customer Confirms | the reply is only list + `ok ou não?`; no file before ok; não discards; other text replaces; neutral one-sentence failures | PASS |
| IV. Closest Match, Exact First | exact forms win; otherwise highest similarity, no floor, ties by Excel order; same product summed; list in Excel order | PASS |
| V. Deterministic Core, LLM Only to Read | the LLM only extracts; matching, summing, rendering, reply reading and Excel are deterministic; LLM injected; LCEL | PASS |
| VI. Orders Are Persisted | `pedidos` per phone with message, list, answer and state; forward-only transitions; no keys stored | PASS |
| VII. Scope | channel-agnostic engine + chat page; no WhatsApp, voice/image, header, prices, memory, aliases, owner UI | PASS |
| Tech: Postgres only, `DATABASE_URL`, schema `pedido`, no pgvector, configurable LLM, Excel rules | see research D4, D6, contracts | PASS |

Post-design re-check: **PASS**, no violations. Deliberate note: Principle IV removes the safety nets of
001/002 on purpose (owner decision); the customer reading the official names is the only check.

## Project Structure

### Documentation (this feature)

```text
specs/003-bot-whatsapp-simples/
├── plan.md  research.md  data-model.md  quickstart.md
├── contracts/ (http-api.md, replies.md)
├── checklists/requirements.md
└── tasks.md            # /speckit-tasks output (NOT created here)
```

### Source Code (repository root)

```text
src/pedido/
├── config.py          # SIMPLIFIED: DATABASE_URL, LLM_* only (thresholds, EMBED_*, MEMORY_* removed)
├── messages.py        # REWRITTEN: the exact replies of the bot and the page labels
├── normalize.py       # KEPT (+ variants file gets "7" -> "sete")
├── catalog.py         # KEPT (variants, Excel order key)
├── match.py           # REWRITTEN: Matcher.closest(text) -> Product (exact first, then best score)
├── extract.py         # SIMPLIFIED: items {texto, quantidade}; no unit field, no examples; retry kept
├── lista.py           # NEW: aggregate(items) -> [(Product, qty)] in Excel order; render(items) -> text
├── conversa.py        # NEW: interpret(text) -> ok|nao|pedido; Conversa.responder(phone, text) -> Resposta
├── chains.py          # REWRITTEN: build_order_chain (extract|match|aggregate) and the export chain
├── export.py          # KEPT
├── llm.py             # KEPT
├── db.py  schema.sql  # SIMPLIFIED: no vector; new tables; guarded cleanup of the old ones
├── store.py           # REWRITTEN: pedidos (create/replace pending, get pending, set state)
├── startup.py         # SIMPLIFIED: DATABASE_URL and LLM_PROVIDER only
├── __main__.py        # KEPT
└── web/app.py         # REWRITTEN: POST /api/mensagem, GET planilha, chat page
    web/templates/index.html, web/static/{app.js,app.css}   # REWRITTEN: the simple chat page
REMOVED: validate.py  memory.py  reprocess.py  embeddings.py
tests/  # migrated or replaced; see tasks.md for the full list of removed test files
```

**Structure Decision**: same single package; the engine (`conversa.py`) knows nothing about HTTP, so
the future WhatsApp adapter will call `Conversa.responder` directly.

## Complexity Tracking

No constitution violations to justify. The reduction of safeguards is the intended change.
