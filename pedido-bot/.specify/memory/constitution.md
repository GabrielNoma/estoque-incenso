<!--
Sync Impact Report
- Version change: 2.3.0 → 2.4.0 (MINOR: a scope and a read-only route added; nothing removed)
- Modified principles:
  - IX. Controlled Access — a third scope, `historico` (read-only listing of the stored orders), kept apart
    from `conversa` because it exposes the orders of EVERY conversation and the WhatsApp key must not have it
  - VII. Simplicity and Scope Discipline — in scope now: read-only listing of the orders for the stock system;
    editing or deleting orders through the API stays out of scope
- Unchanged: I to VI, VIII
- Deferred/TODO placeholders: none
- Source: approved direction of 2026-11-23 (order history screen in the stock system)
-->
# Pedido WhatsApp → Excel Constitution

## Core Principles

### I. Brazilian Portuguese Everywhere (NON-NEGOTIABLE)
Everything the customer sees or the system generates for the customer MUST be in Brazilian
Portuguese (pt-BR): every reply, the test chat page, error notices, and LLM prompts. Code identifiers
and internal documentation MAY be in English. No user-facing string may be hard-coded in another
language.

**Rationale**: the customers and the order form are Brazilian; an English or mixed conversation would
confuse the person who confirms the order.

### II. Test-First (NON-NEGOTIABLE)
Tests MUST be written before the code they cover and MUST be observed failing for the right reason
before implementation begins (red → green → refactor). Every implementation task in a plan MUST be
preceded by its test task. Deterministic stages (matching, nickname lookup, summing, ordering,
formatting the list, reading the customer's reply, validating the model's output, limits, filling the
Excel) MUST be testable without network access. The LLM and the embedding model MUST be testable
through injected stubs with canned responses and, for the provider adapters, through a fake
OpenAI-compatible server, so that no test needs the internet. Tests that touch the database MUST run
against a real Postgres with pgvector (Docker), never against a substitute engine. The synthetic pt-BR
regression messages MUST exist before the stages they exercise are implemented.

**Rationale**: the order the customer confirms ends up in a wholesale spreadsheet; only tests written
first keep matching, summing, ordering and the guardrails honest.

### III. The Customer Confirms
The customer is the only reviewer. The bot MUST reply to an order with the plain list of the matched
products and their quantities and end the reply with "ok ou não?". Nothing MUST be written to the
Excel, and no file MUST be sent, before the customer replies ok. "não" MUST discard the pending order;
any other text MUST be read as a new order that replaces the pending one. The bot MUST NOT ask
anything other than "ok ou não?", MUST NOT offer options, and MUST NOT point out doubts or
approximations in the list. When something fails (the language model is unavailable, the file cannot be
generated) or a guardrail stops a message, the reply MUST be one short neutral sentence that tells the
customer what to do next. When the order-form MODEL cannot be used (it cannot be read, it has no
products, or a product of the pending order is not in the active model when the Excel is filled), the
reply MUST be one short neutral sentence telling the customer to check the model, the pending order MUST
be kept, and nothing MUST be invented. This does not change the matching: a written wording is still
always matched to the closest product of the active model, and the bot still never reports doubts about
wording. There is no owner review screen, candidate selection or merge control.

**Rationale**: the customer knows what they ordered; a plain list with the official product names is
the cheapest and clearest check, and the conversation stays as short as a chat should be.

### IV. Closest Match, Exact First
Every extracted item MUST be matched to a product of the catalog, which is ALWAYS derived from the ACTIVE
model and reloaded when a model is activated, trying in this order:
1. **Exact wording**: a normalized wording equal to a catalog name, to its abbreviation expansions, or
   to one of its full-wording variants of an ambiguous abbreviation (for example "S." as santo, santa
   or saúde, and "7" as "sete"). An exact wording MUST win over everything below.
2. **Learned nickname**: a written wording that customers confirmed for that product in at least 2
   orders in the state confirmado (the same customer counts). A nickname is found by its exact
   normalized text first and then by embedding similarity above a high, configurable threshold. Negative
   signals (recusado, substituido) MUST NOT delete a nickname; they reduce its confidence, and a
   nickname MUST stop applying when its negative signals reach its positive ones. A nickname MUST NOT
   override an exact wording. A nickname stores the product NAME it was confirmed for; when a model is
   activated, every nickname whose product no longer exists or whose product name changed MUST be
   disabled (status desativado) and MUST NOT be deleted.
3. **Closest product**: the highest similarity, whatever the score (there is no similarity floor), and
   ties MUST be broken by the Excel order so the result is deterministic.

Quantities of items that match the same product MUST be summed. The list MUST follow the Excel order
and show quantities in dozens. When the memory cannot be read, matching MUST fall back to steps 1 and 3
without any visible change.

**Rationale**: the catalog has near-identical names, so exact wordings must never lose to an
approximation; what customers have repeatedly confirmed is a safer guess than raw similarity; and the
customer reading the official names stays the safety net.

### V. Deterministic Core, LLM Only to Read
The only model that reads orders MUST be the LLM that extracts the items (written text and quantity in
dozens, converting other units to dozens in the prompt), and it MUST NEVER write text for the customer.
An embedding model MAY be used ONLY to look up and to store learned nicknames. Both models MUST be
injected, never constructed inside a stage, and configurable (`LLM_*` and `EMBED_*`, OpenAI-compatible,
for example a local Ollama in development and a hosted service in production). The embedding vector size
MUST be requested from the service when it supports it (`EMBED_DIMENSIONS` sent as `dimensions` when
`EMBED_SEND_DIMENSIONS=true`). Vectors of different models are never compared, so switching the embedding
model keeps exact-text nicknames working and only pauses similarity matching until the wordings are
confirmed again with the new model. Everything else MUST be plain deterministic Python: matching, nickname
rules, summing, ordering, formatting, reading the customer's reply (ok, não, anything else), the
guardrails, and filling the Excel. The pipeline MUST be composed of LangChain LCEL Runnables, with
deterministic stages wrapped as `RunnableLambda`, so each stage is unit-testable without the network.
There is no LLM tie-break and no LLM-generated reply.

**Rationale**: a model in every step makes failures untraceable and tests flaky; reading free text is
the one job only a model can do, and similarity lookup is the only job an embedding is needed for.

### VI. Orders Are Persisted
Every order message, the list sent to the customer, the customer's answer and the state of the order
(aguardando, confirmado, recusado, substituido) MUST be stored in Postgres per phone number, so a
pending order survives a restart and a confirmed order can always be regenerated. The state MUST only
move forward: aguardando → confirmado, recusado or substituido. The nickname memory (the written
wording, its normalized form, the product, the embedding and the name of the embedding model, the
product name, the positive and negative counts and the status) MUST be stored in the same Postgres, with the `vector`
extension, and the embedding dimension MUST be configurable and fixed when the memory table is created.
The memory MUST be written AFTER the reply is produced and MUST NOT change or delay what the customer
sees; a failure to write or to read it MUST be silent and MUST NOT break the conversation. The order-form models (the file, its name, its version and which one is active) MUST be stored in the
same Postgres with their previous versions kept. The schema MUST evolve ONLY through ordered, versioned migration files applied by a separate command
(never implicitly at every start). The application MUST record the applied versions with a checksum, MUST
refuse to start in production when migrations are pending or when an applied migration file changed, and
a migration MUST NOT drop data without an explicit comment and a backup note. The current `schema.sql`
becomes the baseline migrations. API keys MUST never be stored.

**Rationale**: a conversation has state, and losing the pending list would make "ok" meaningless; a
memory written out of the customer's sight lets the bot improve without lengthening the chat.

### VII. Simplicity and Scope Discipline (YAGNI)
In scope: the conversation engine (channel-agnostic: it receives a phone number and a text and
returns a reply text and an optional file), the web test chat page, exact and closest matching, the
silent nickname memory, the guardrails, summing, the Excel in order, and sending the Excel after ok, and exporting and importing the order-form model through the API
(download, validated upload, information about the active model), and the production readiness of the
bot service (access control, health check, versioned migrations, hosted embeddings, hosting configuration,
Dockerfile) with the contract the stock system uses.
The service API for the stock system (keys and `/v1` routes) and the real WhatsApp adapter are the
NEXT features. Out of scope and MUST NOT be built without an amendment or a new spec: the WhatsApp adapter itself (only
its public route is reserved), user sign-in or user accounts, a billing system, the stock system's own login,
a real WhatsApp
connection, voice or image input, customer header data and a client store, prices and discounts, a
screen inside this project (the screen that uses the API lives in the stock system), restoring an older
model through the API (versions are kept in the database for a manual restore), an
owner screen to review or edit nicknames (they are managed by script or SQL for now), nicknames typed
by hand, and fine-tuning. Complexity MUST be justified in the plan.

**Rationale**: the product is a short conversation that returns an Excel; every extra feature would
make that conversation longer or riskier.

### VIII. Guardrails for the Model
The model MUST be kept to its one purpose, reading orders. The customer's message is data, never
instructions: the prompt MUST delimit it and state that instructions inside it are ignored. The model's
output MUST be validated against `{texto, quantidade}`: at most a configurable number of lines per
message, a maximum length of text per line, and a quantity that is a number greater than zero; invalid
lines MUST be dropped silently. After summing, a quantity above 1000 dozens of ONE product MUST make
the bot reply one short neutral sentence asking to send the order again with a smaller quantity, and
nothing MUST be stored as pending for that message. There MUST be a maximum message length and a
per-phone rate limit (both configurable); exceeding either MUST get one short neutral sentence. There
MUST be no path for the model to produce text for the customer, and memory MUST never be put in the
prompt as instructions. The cost and abuse guards MUST also include: a daily message limit per conversation (configurable,
default 200), an explicit maximum output size for every call to the language model (configurable), a rate
limit per API key (configurable, default 120 requests per minute), a maximum request body size, and a
maximum number of concurrent language model calls (configurable, default 4), so that a burst cannot run
up the bill. Each activation of a guardrail MUST be logged by type only, never with the
message content or any secret.

**Rationale**: a model that reads text from strangers can be talked into other jobs; limits that sit
outside the model keep it predictable, cheap and harmless.

### IX. Controlled Access
Every route of the API MUST require an API key, sent as `Authorization: Bearer <key>` or `X-API-Key`,
except the public routes. The only exception is local development with NO key configured, where the
application starts with a visible warning; in production it MUST refuse to start without at least one key. The keys MUST come ONLY from the environment (a list of named keys, each with
scopes), MUST be compared in constant time, and MUST NEVER be stored in the database or logged. A missing or
invalid key MUST get 401, and a key without the needed scope MUST get 403, both as a pt-BR JSON error, and
each MUST be logged by TYPE only. The scopes are `conversa` (send messages, download order files) and
`modelo` (export and import the model and read its information); `historico` (read-only listing of the
stored orders of every conversation, with their order files). The ONLY public routes are the health
check (`GET /saude`, which returns no data) and, in a later feature, the WhatsApp webhook (protected by its
own signature verification). The test chat page and the OpenAPI documentation MUST be switchable off and
MUST be off when `ENVIRONMENT=producao`. In production the application MUST bind to `0.0.0.0` and the port
of the `PORT` variable, and locally to `127.0.0.1:8000`. No CORS is opened.

**Rationale**: a hosted bot spends money on every message and holds the order model; only requests with a
key and the right scope may reach it.

## Technology Constraints

- Language and app: Python with FastAPI, serving a simple test chat page and JSON endpoints.
- Database: Postgres is the ONLY database. `DATABASE_URL` is required. All tables live in the schema
  `pedido`. The `vector` extension (pgvector) is REQUIRED for the nickname memory. Locally it runs
  through docker compose with the `pgvector/pgvector:pg16` image; Supabase is adopted later by changing
  only the connection string, with row-level security enabled and no policies so the REST API exposes
  nothing.
- Orchestration: LangChain LCEL Runnables.
- LLM: configurable provider (`LLM_PROVIDER` = `anthropic` | `openai_compatible`, with `LLM_MODEL`
  and `LLM_BASE_URL`); API keys only from the environment, never written to the repository or
  database.
- Embeddings: configurable OpenAI-compatible service (`EMBED_BASE_URL`, `EMBED_MODEL`, `EMBED_API_KEY`,
  and the dimension), keys only from the environment. Without it the bot works with steps 1 and 3 of
  the matching.
- Template (the model): the original `PLANILHA 2024.xls` MUST be kept untouched; it was converted once to
  `.xlsx`, and that copy (`assets/PLANILHA_2024.xlsx`) is only the SEED used when the database has no
  model yet. The models live in Postgres with versions; exactly one is active and the catalog is derived
  from it. Delivered files are `.xlsx`. Only the quantity cells are written and every formula is
  preserved. The product-to-cell mapping MUST be verified by reading the produced file back against the
  catalog. A new model uploaded through the API MUST be validated before it becomes active: a readable
  `.xlsx`, at least one product in the same layout (names in columns C, G, K, O, S of rows 4 to 46, the
  quantity cell two columns to the left), no duplicated normalized names, no merged quantity cells, and a
  maximum size (configurable, default 5 MB). An invalid model MUST be rejected with a Portuguese message
  saying to check the model, and the active model MUST stay unchanged. Previous models MUST be kept.
- Hosting: the service runs from a container (`Dockerfile`), reads every setting from the environment
  (`ENVIRONMENT`, `PORT`, `DATABASE_URL`, `LLM_*`, `EMBED_*`, `API_KEYS`), exposes `GET /saude` for the
  platform's health check, and applies migrations through a separate command before the new version starts.
- The project has no git repository; this MUST NOT be assumed in tooling or tasks.

## Development Workflow

The project follows Spec-Driven Development with Spec Kit, in this order: constitution →
specify → (clarify) → plan → tasks → (analyze) → implement. Each feature gets its own spec, plan, and
tasks: `001-pedido-intake-excel` and `002-rag-memory-providers` are the earlier design, partly
superseded by `003-bot-whatsapp-simples` (the simple order bot). `004-memoria-e-guardrails` (the silent
nickname memory and the guardrails) comes after 003; `005-modelo-planilha` (the managed order-form model)
comes after 004; `006-producao-e-acesso` (production readiness: access control, versioned migrations,
hosted embeddings, cost guardrails, hosting) comes after 005 and before the WhatsApp adapter. The stock system (estoque-incenso) gets its own feature with the chat screen that
consumes this API; the service API with keys and then the WhatsApp adapter come later. Plans MUST include a Constitution Check against the principles above,
and task lists MUST place each test task before its implementation task.

## Governance

This constitution supersedes other project practices. Amendments are made only through
`/speckit-constitution`, and each amendment MUST update the Sync Impact Report and bump the version:
MAJOR for removing or redefining a principle, MINOR for adding a principle or materially expanding
guidance, PATCH for clarifications and wording. Every plan and review MUST verify compliance with
these principles; any deviation MUST be written down and justified in the plan's complexity
tracking. Principles I and II are non-negotiable and MUST NOT be waived by a plan.

**Version**: 2.4.0 | **Ratified**: 2026-10-23 | **Last Amended**: 2026-11-23
