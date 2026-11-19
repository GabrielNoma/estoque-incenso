# Implementation Plan: Memória silenciosa de apelidos e guardrails

**Branch**: `004-memoria-e-guardrails` (no git repository; folder name only) | **Date**: 2026-11-16 | **Spec**: [spec.md](spec.md)

**Input**: Feature specification from `/specs/004-memoria-e-guardrails/spec.md`

## Summary

Two additions to the 003 bot, both invisible in the customer's reply. (1) **Nickname memory**: when the
customer says ok, the written wording of every line is stored (normalized, with an embedding, with the
product, a positive count); refused or replaced orders add a negative count to wordings that already
exist; a wording confirmed at least 2 times (and with more positives than negatives) becomes a learned
nickname. Matching becomes: exact wording → learned nickname (exact text, then embedding similarity above
a high threshold) → closest product. The memory is written after the reply, in a background worker, and
every memory failure is silent. (2) **Guardrails**: the message is delimited as data in the prompt, the
model's output is validated, a quantity above 1000 dozens of one product is refused with a neutral
sentence, and there are limits on message size and messages per phone per minute; activations are logged
by type only. A script lists, disables and enables nicknames. See [research.md](research.md).

## Technical Context

**Language/Version**: Python 3.11 (`uv`, as before)

**Primary Dependencies**: as 003 (FastAPI, LangChain LCEL, `langchain-openai`, `rapidfuzz`, `openpyxl`,
`psycopg[binary]`) **plus** `pgvector` (the Python adapter, to send and read vectors).

**Storage**: Postgres 16 with the `vector` extension (the `pgvector/pgvector:pg16` image already in use);
schema `pedido`; new table `apelidos`; table `pedidos` gets one column. Hosted Supabase later by changing
`DATABASE_URL` only.

**Testing**: pytest on a real Postgres with pgvector; injected stubs for the chat model and for the
embedder; a fake OpenAI-compatible server (chat **and embeddings**) for the adapters; no test needs the
internet.

**Target Platform**: the user's computer (macOS), as before.

**Project Type**: web-service (single project).

**Performance Goals**: the reply time stays that of 003; the memory read adds at most the embedding call
(skipped when no nickname exists, and disabled for the rest of a message after the first failure); the
memory write is off the reply path.

**Constraints**: replies byte-identical to 003 except for the product a nickname changes; every limit
configurable; embedding wait at most `EMBED_TIMEOUT_SECONDS` (default 5); keys only from the environment;
logs hold only guardrail types.

**Scale/Scope**: one business, tens of conversations a day, 167 products, hundreds of nicknames.

## Constitution Check

*GATE: passed before Phase 0; re-checked after Phase 1.* Constitution **v2.1.0**.

| Principle / constraint | Gate | Status |
|---|---|---|
| I. pt-BR everywhere | the three new neutral sentences and the script's output live in `messages.py`; the scanner test covers them | PASS |
| II. Test-First | each module's tests first (RED observed); real Postgres with pgvector; embedder and chat stubs; fake server with embeddings | PASS (tasks ordering) |
| III. The Customer Confirms | replies unchanged; guardrail stops are one neutral sentence | PASS |
| IV. Closest Match, Exact First | order exact → nickname (≥2 positives, positives > negatives, active; exact text then similarity ≥ threshold) → closest; nickname never beats an exact wording | PASS |
| V. Deterministic Core, LLM Only to Read | the LLM only reads; the embedder only looks up and stores; both injected; nickname rules are plain Python | PASS |
| VI. Orders Are Persisted | `apelidos` in the same Postgres with vector, model name, counts, status; written after the reply; failures silent | PASS |
| VII. Scope | no owner screen, WhatsApp, service API, hand-typed nicknames, memory in the prompt | PASS |
| VIII. Guardrails for the Model | delimited data, validated output, 1000 dz cap, size and rate limits, type-only logs, no path for model text | PASS |
| Tech: pgvector required, `EMBED_*` returns, schema `pedido` | see research D3, D4 and contracts | PASS |

Post-design re-check: **PASS**, no violations.

## Project Structure

### Documentation (this feature)

```text
specs/004-memoria-e-guardrails/
├── plan.md  research.md  data-model.md  quickstart.md
├── contracts/ (configuration.md, replies.md, script.md)
├── checklists/requirements.md
└── tasks.md            # /speckit-tasks output (NOT created here)
```

### Source Code (repository root)

```text
src/pedido/
├── config.py        # + limits and EMBED_* settings (all from the environment, with defaults)
├── messages.py      # + MENSAGEM_LONGA, MUITAS_MENSAGENS, QUANTIDADE_ALTA, startup text for pgvector, script text
├── embeddings.py    # NEW: OpenAI-compatible embedder (injected, short timeout, never raises to the caller's flow)
├── memoria.py       # NEW: Memoria: buscar (lookup), aprender (positives), penalizar (negatives), background writer
├── guardrails.py    # NEW: validar_linhas, checar_quantidade, checar_tamanho, RateLimiter, log-by-type
├── extract.py       # prompt delimits the message as data; output goes through the validation
├── match.py         # Matcher takes an injected nickname lookup: exact → nickname → closest
├── lista.py         # aggregate also keeps the written wordings of each product
├── chains.py        # order chain returns the aggregated items AND the matched lines (wording, product)
├── conversa.py      # rate limit, size limit, quantity cap; after ok/não/replace: schedule memory writes
├── db.py schema.sql # vector extension, table apelidos with the configured dimension, pedidos.linhas
├── store.py         # apelidos CRUD, similar lookup, status; pedidos.linhas
├── startup.py       # EMBED_* checks; refuses to start if the memory cannot be prepared
└── web/app.py       # builds the embedder and the Memoria from the environment
scripts/apelidos.py  # NEW: list, --desativar ID, --ativar ID
tests/               # new unit/integration tests; fakes.py gains an embeddings route and FakeEmbedder
```

**Structure Decision**: same single package. The memory is a collaborator injected into the `Matcher`
(lookup) and the `Conversa` (writes), so the engine stays channel-agnostic and every piece is testable
with stubs.

## Complexity Tracking

No constitution violations to justify.
