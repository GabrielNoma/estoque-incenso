# Feature Specification: Produção e acesso

**Feature Branch**: `006-producao-e-acesso` (no git repository; folder name only)

**Created**: 2026-11-18

**Status**: Draft

**Input**: User description: "Production readiness of the order bot, which will run hosted, be consumed by the stock system and later by a WhatsApp adapter: controlled access, health check and hosting, versioned migrations, hosted embeddings, cost and abuse guardrails, and the contract for consumers. Constitution v2.3.0."

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Only requests with a key can use the API (Priority: P1)

Whoever consumes the API (the stock system, later the WhatsApp adapter) sends a key. Without a valid key,
nothing answers data. Each key has a name and scopes: **conversa** (send messages, download order files) and
**modelo** (export and import the model, read its information). A key without the scope a route needs is
refused. In production the test chat page and the API documentation do not exist.

**Why this priority**: a hosted bot spends money on every message and holds the order model.

**Independent Test**: call every route with no key, a wrong key, a key without the scope and a right key, in
a configuration with keys and one without.

**Acceptance Scenarios**:

1. **Given** keys are configured, **When** any route other than the health check is called with no key or a
   wrong key, **Then** the answer is 401 with a Portuguese JSON error and no data.
2. **Given** a key with only the conversa scope, **When** the model routes are called, **Then** the answer
   is 403 with a Portuguese JSON error; and a key with only the modelo scope is refused on the message and
   file routes.
3. **Given** a key with the right scope, sent as `Authorization: Bearer` or as `X-API-Key`, **When** the
   route is called, **Then** it works exactly as before.
4. **Given** production, **When** the test chat page, its static files, `/docs`, `/redoc` or `/openapi.json`
   are requested, **Then** each answers 404.
5. **Given** production with no valid key configured, **When** the application starts, **Then** it refuses
   to start with a Portuguese message saying that keys are required.
6. **Given** no key configured outside production, **When** the application starts, **Then** it starts with
   a visible warning and access control is off, so local use and tests keep working.
7. **Given** any refusal, **When** the log is read, **Then** it holds only the type (missing, invalid,
   scope) and the key's name when known, never the key.
8. **Given** a request, **When** a page from another origin tries to call the API from a browser, **Then**
   no cross-origin permission is granted.

---

### User Story 2 - Health check and hosting (Priority: P1)

The hosting platform asks `GET /saude` to know whether the service is alive. It answers `{"status":"ok"}`
when the application and the database answer and `{"status":"indisponivel"}` with 503 otherwise, never any
detail, and needs no key. In production the application listens on all addresses and on the port the
platform gives; locally only on the same machine. A container recipe and a hosting example are provided.

**Why this priority**: the platform restarts or routes by this answer, and the service must start there.

**Independent Test**: call the health check with the database up and down; start the application with the
`PORT` setting; build the container and run it.

**Acceptance Scenarios**:

1. **Given** the database answers, **When** `GET /saude` is called with no key, **Then** it answers 200
   `{"status":"ok"}` and nothing else.
2. **Given** the database does not answer, **When** `GET /saude` is called, **Then** it answers 503
   `{"status":"indisponivel"}` with no detail.
3. **Given** production and `PORT=10000`, **When** the application starts, **Then** it listens on all
   addresses on port 10000; locally it listens only on 127.0.0.1:8000.
4. **Given** the container recipe, **When** the image is built, **Then** it runs as a non-root user, holds
   no secret and no `.env`, and every setting comes from the environment.
5. **Given** the hosting guide, **When** a person follows it, **Then** the variables, the migration step and
   the first-deploy checklist are all listed.

---

### User Story 3 - The database changes only through versioned migrations (Priority: P1)

The schema evolves through ordered migration files applied by a separate command, each in its own
transaction, recording version and checksum. The current schema becomes the baseline (0001, safe to apply
on an existing development database); the second migration (0002) adds the table for the daily limit. The
application refuses to start in production when migrations are pending or when an applied file changed.

**Why this priority**: a hosted database cannot be changed by the application at every start, and a change
of schema must be traceable.

**Independent Test**: apply the migrations to an empty database, to a copy of the current development
database and again; alter an applied file; start the application in each state.

**Acceptance Scenarios**:

1. **Given** an empty database, **When** the migration command runs, **Then** every pending migration is
   applied in order and each is recorded with its version and checksum.
2. **Given** the migrations already applied, **When** the command runs again, **Then** nothing changes.
3. **Given** the current development database (with orders, models and nicknames), **When** the command
   runs, **Then** the baseline is adopted without losing any row.
4. **Given** production and a pending migration, **When** the application starts, **Then** it refuses with a
   Portuguese message telling to run the migration command.
5. **Given** an applied migration file that was changed afterwards, **When** the application starts in
   production, **Then** it refuses with a Portuguese message naming the file.
6. **Given** outside production, **When** migrations are pending, **Then** the application refuses too,
   unless the setting that allows migrating at start is on.
7. **Given** a status request, **When** the command runs with the status option, **Then** it lists each
   migration as applied, pending or changed, and changes nothing.
8. **Given** the vector size configured differs from the one the memory table was created with, **When**
   the application starts, **Then** it still refuses with the existing Portuguese message.

---

### User Story 4 - Hosted embeddings and re-indexing (Priority: P1)

The embedding service can be any OpenAI-compatible hosted service. When the setting asks for it, the
configured vector size is sent in the request so the service returns vectors of the size of the memory
table. A vector of another size is still discarded. Changing the embedding model keeps the exact-text
nicknames working and only pauses similarity matching, because vectors of different models are never
compared. A command-line option recomputes the embedding of every stored nickname with the current model.

**Why this priority**: the local model used in development does not exist in production.

**Independent Test**: point the memory to a fake hosted service; check the request, switch the model, run
the re-indexing option.

**Acceptance Scenarios**:

1. **Given** the dimension setting is on, **When** an embedding is requested, **Then** the request carries
   the configured size; when it is off, the request carries none.
2. **Given** a vector of another size, **When** it comes back, **Then** it is discarded and the reply is
   produced without the memory.
3. **Given** nicknames learned with model A and the configuration switched to model B, **When** an order
   arrives, **Then** exact-text nicknames still apply and similarity matching uses only model B vectors.
4. **Given** the re-indexing option, **When** it runs, **Then** every nickname gets an embedding of the
   current model, nothing is deleted, and the count of done and failed is printed in Portuguese.
5. **Given** the embedding service fails during re-indexing, **When** it finishes, **Then** the failures are
   counted and the successes are kept.
6. **Given** no embedding configuration, **When** the application runs, **Then** the memory stays off.

---

### User Story 5 - Cost and abuse guardrails (Priority: P1)

A conversation has a daily message limit, kept in the database so it survives restarts and several
instances. Every call to the language model has an explicit maximum output size. Each key has a request rate
limit. Requests have a maximum body size. The number of language model calls at the same time has a cap; a
message that cannot get a slot soon gets one short neutral sentence. Every activation is logged by type.

**Why this priority**: a burst or an abuse must not run up the bill of the language model.

**Independent Test**: send more messages than each limit and check the answers, the number of model calls
and the logs.

**Acceptance Scenarios**:

1. **Given** a conversation that already sent 200 messages today, **When** it sends another, **Then** it
   gets one short neutral Portuguese sentence, the language model is not called, and the pending order is
   kept; the next day it works again.
2. **Given** several instances or a restart, **When** the count is read, **Then** it is the same (it is
   stored in the database).
3. **Given** any call to the language model, **When** it is made, **Then** it carries the configured maximum
   output size (default 4096).
4. **Given** a key sent more requests in a minute than its limit (default 120), **When** the next arrives,
   **Then** it gets 429 with a Portuguese JSON error; other keys are not affected.
5. **Given** a message request body above 64 KB, **When** it arrives, **Then** it is refused with 413 and a
   Portuguese JSON error before the language model is called; the model upload keeps its own limit.
6. **Given** more simultaneous messages than the cap (default 4), **When** they arrive together, **Then** at
   most that many language model calls run at once, and a message that waits more than the short limit
   (default 20 seconds) gets one short neutral sentence asking to try again in a moment.
7. **Given** any guardrail acting, **When** the log is read, **Then** it holds only the type, never message
   text, phone numbers or keys.

---

### User Story 6 - Documented contract for consumers (Priority: P2)

The repository documents the API contract (keys, scopes, errors, examples) and a hosting guide with the
variables, the migration step before every deploy, the health check path and a first-deploy checklist. The
change the stock system needs (sending the key from its backend, from an environment variable) is written as
a requirement for that repository.

**Why this priority**: the stock system and the WhatsApp adapter need a stable agreement; the deploy needs a
repeatable list.

**Independent Test**: follow the documents on a clean machine and call the examples.

**Acceptance Scenarios**:

1. **Given** the contract document, **When** an example call is run, **Then** it works against a running bot.
2. **Given** the hosting guide, **When** the checklist is followed, **Then** the service starts with the
   migrations applied and the health check answering.
3. **Given** the stock requirement, **When** the stock repository reads it, **Then** it states the variable
   names, the header and the scopes the stock key needs.

---

### Edge Cases

- Two keys with the same name, a malformed entry, or a key shorter than 32 characters in the list: the
  application refuses to start with a Portuguese message naming the entry (never the key).
- A route that needs no key by mistake: a test lists every route and its required scope, so a new route
  without a rule fails the test.
- `Authorization` and `X-API-Key` both present: `Authorization` wins.
- The day changes while a conversation is active: the count restarts at the new day (the day is the
  server's date in the business timezone, America/Sao_Paulo).
- A daily limit reached by a conversation id does not block other ids.
- Health check while migrations are pending: it still answers 200 only when the database answers; a
  pending migration stops the start in production anyway.
- A key's rate limit counts refused requests as not counted (the block ends when the window slides).
- A migration that fails halfway: its transaction is rolled back, nothing is recorded, and the command
  stops with a Portuguese message.
- The re-indexing option with no embedding configured: refuses with a Portuguese message.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: Every route MUST require an API key sent as `Authorization: Bearer <key>` or `X-API-Key`,
  except `GET /saude`; when both headers are present, `Authorization` wins.
- **FR-002**: Keys MUST come only from the environment as a comma-separated list of `name:scopes:key`
  (scopes joined with `+`), each key with at least 32 characters; a malformed or duplicated entry or a short
  key MUST stop the start with a Portuguese message that never shows the key.
- **FR-003**: Keys MUST be compared in constant time and MUST NEVER be stored in the database or logged.
- **FR-004**: The scopes are `conversa` (message and order-file routes) and `modelo` (model routes); a
  missing or invalid key MUST get 401 and a key without the scope MUST get 403, both as
  `{"erro","mensagem"}` in Portuguese, logged by type only.
- **FR-005**: In production the test chat page, its static files and the API documentation MUST answer 404,
  and the application MUST refuse to start without at least one valid key.
- **FR-006**: Outside production with no key configured the application MUST start with a visible warning
  and access control MUST be off; with keys configured it MUST be on everywhere.
- **FR-007**: No cross-origin permission MUST be opened.
- **FR-008**: `GET /saude` MUST answer 200 `{"status":"ok"}` when the application and the database answer
  and 503 `{"status":"indisponivel"}` otherwise, with no key and no detail.
- **FR-009**: In production the application MUST listen on all addresses and on the port of the `PORT`
  setting; otherwise only on 127.0.0.1:8000.
- **FR-010**: A container recipe (non-root user, no secret inside, an ignore file) and a hosting example
  with the table of environment variables MUST be provided.
- **FR-011**: The schema MUST evolve only through ordered migration files applied by a separate command that
  applies the pending ones in order, each in its own transaction, recording version and checksum, with a
  status option; applying twice MUST change nothing.
- **FR-012**: The current schema MUST become the baseline migration (safe on an existing database), and a
  second migration MUST add the daily-usage table (conversation, day, number of messages).
- **FR-013**: The application MUST refuse to start in production when migrations are pending or an applied
  file changed, and outside production too unless migrating at start is explicitly allowed by a setting,
  always with a Portuguese message that tells what to do.
- **FR-014**: The vector size MUST come from `EMBED_DIMENSIONS` when the baseline is applied; a different
  configured size later MUST still be refused with the existing message.
- **FR-015**: A migration MUST NOT drop data without an explicit comment and a backup note in the file.
- **FR-016**: The embedding service MAY be any OpenAI-compatible hosted service; when `EMBED_SEND_DIMENSIONS`
  is on, the configured size MUST be sent with the request; a vector of another size MUST be discarded.
- **FR-017**: Vectors of different models MUST never be compared; exact-text nicknames MUST keep working
  after a model switch.
- **FR-018**: The nicknames script MUST have a re-indexing option that recomputes every stored nickname's
  embedding with the current model, deletes nothing, and prints how many were done and how many failed in
  Portuguese.
- **FR-019**: A conversation MUST have a daily message limit (default 200, configurable) stored in the
  database; the message over the limit MUST get one short neutral Portuguese sentence without calling the
  language model and without losing the pending order.
- **FR-020**: Every call to the language model MUST carry an explicit maximum output size (default 4096,
  configurable).
- **FR-021**: Each key MUST have a request rate limit (default 120 per minute, configurable) answered with
  429 and a Portuguese JSON error.
- **FR-022**: A message request body above 64 KB MUST be refused with 413 before the language model is
  called; the model upload keeps its own limit.
- **FR-023**: At most the configured number of language model calls (default 4) MUST run at the same time;
  a message that cannot get a slot within a short wait (default 20 seconds) MUST get one short neutral
  Portuguese sentence.
- **FR-024**: Every guardrail and access activation MUST be logged by type only, never message text, phone
  numbers or keys.
- **FR-025**: The API contract and a hosting guide MUST be documented in the repository, with the
  requirement for the stock system (the variable names, the header and the scopes of its key).
- **FR-026**: A test MUST list every route with its required scope so that a new route without a rule
  fails.
- **FR-027**: All text the user sees MUST be in Brazilian Portuguese, and the replies for normal orders MUST
  NOT change.
- **FR-028**: The system MUST NOT include, in this version: the WhatsApp adapter, user sign-in or accounts,
  a billing system, the stock system's own login, or the real deployment.

### Key Entities *(include if feature involves data)*

- **API key**: a name, its scopes and the secret, read only from the environment.
- **Migration**: an ordered file with a version and a checksum, recorded when applied.
- **Daily usage**: for a conversation and a day, the number of messages received.
- **Embedding configuration**: service address, model, key, vector size and whether the size is sent.
- **Guardrail limits**: daily messages, request rate per key, body size, concurrent model calls and maximum
  output size.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: In 100% of tests, with keys configured, no route other than the health check answers data
  without a valid key (401 or 403).
- **SC-002**: In 100% of tests, the test page and the API documentation answer 404 in production.
- **SC-003**: In 100% of tests, the application refuses to start in production without a valid key, with a
  pending migration, or with an applied migration file changed.
- **SC-004**: Applying the migrations twice changes nothing, and an existing development database is
  adopted with every order, model and nickname intact, in 100% of tests.
- **SC-005**: In 100% of tests, the 201st message of a conversation in a day gets the neutral sentence and
  does not call the language model, and works again the next day.
- **SC-006**: In 100% of tests, the 121st request of a key within a minute gets 429, and other keys are
  not affected.
- **SC-007**: In 100% of tests, a burst above the concurrency limit never runs more simultaneous language
  model calls than the limit.
- **SC-008**: In 100% of tests, the embedding request carries the configured size when the setting is on, and
  a vector of another size never reaches the memory.
- **SC-009**: In 100% of tests, the logs of access and guardrails contain no message text, phone number or
  key.
- **SC-010**: The health check answers in under 1 second, with 200 when the database is up and 503 when it
  is down, in 100% of tests.
- **SC-011**: The replies for normal orders are unchanged and every test of the earlier features still
  passes.

## Assumptions

- The business timezone for the daily limit is America/Sao_Paulo.
- The default embedding choice for production is an OpenAI-compatible hosted model that accepts a requested
  vector size (for example `text-embedding-3-small` asked for 1024 numbers); the service is configurable, so
  another one can be used.
- The migration command runs before each deploy (for example as the platform's pre-deploy step); the
  application never migrates by itself in production.
- Rate limits per key and the concurrency cap are kept in memory of each instance; the daily limit is the
  only shared counter (database).
- Anyone holding a key with the modelo scope can replace the model; protecting who may do that in the stock
  system is a requirement for the stock repository, not built here.
- The first production deploy and the WhatsApp adapter are separate steps after this feature.
- The nicknames script, the chat page for local tests and the rest of the earlier features are reused.
