> **Aviso (2026-11-16):** esta especificação foi substituída em parte pela feature `003-bot-whatsapp-simples` (bot simples: lista, ok/não, sem tela de revisão, sem memória RAG). Vale o que está em `specs/003-bot-whatsapp-simples/`.

# Feature Specification: Banco único, serviços de IA configuráveis e memória de pedidos

**Feature Branch**: `002-rag-memory-providers` (no git repository; folder name only)

**Created**: 2026-10-23

**Status**: Draft

**Input**: User description: "Feature 002 for the Pedido WhatsApp → Excel tool (builds on 001-pedido-intake-excel, which already works end to end): a single shared database, configurable AI services, and a memory that learns from the orders the user confirms, used to help match products and read new messages."

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Everything saved in one durable database (Priority: P1)

The user keeps using the tool exactly as in 001, but every order, line, correction and remembered
phrase is now saved in one database that survives restarts and can later be moved to a hosted
service. Nothing is kept in local files. If the database is not configured or cannot be reached, the
tool refuses to start and says so in Portuguese.

**Why this priority**: the memory in the next stories needs a place to live, and a hosted database is
the goal; but the user must not notice any change in daily use.

**Independent Test**: start the tool with a configured database, approve an order, restart the tool,
and verify the history, the remembered phrases and the download are all still there and behave as
in 001. Start it without a database and verify it refuses with a clear Portuguese message.

**Acceptance Scenarios**:

1. **Given** a configured and reachable database, **When** the user pastes a message, reviews and
   approves an order, restarts the tool, and opens the history, **Then** the order appears with
   suggestion and final answer side by side, and its spreadsheet can still be downloaded.
2. **Given** a phrase the user confirmed before a restart, **When** the same wording appears after
   the restart, **Then** it is matched automatically as in 001.
3. **Given** no database configured, **When** the tool is started, **Then** it does not start and
   shows a clear message in Portuguese saying what is missing.
4. **Given** a configured address that cannot be reached, **When** the tool is started, **Then** it
   does not start and shows a clear message in Portuguese that the database is unreachable.
5. **Given** the database becomes unreachable while the tool is running, **When** the user tries an
   action, **Then** they see a clear message in Portuguese, no order is left half-saved, and the tool
   works again once the database is back.
6. **Given** any action in the tool, **When** it completes, **Then** no data was written to local
   files other than the downloaded spreadsheet.

---

### User Story 2 - Choose the AI services by configuration (Priority: P1)

The user chooses which language model service reads the messages, and which service turns text into
similarity vectors, by configuration alone: service address, model name, and a key taken from the
environment. At least two choices exist for the language model: the current Claude service, or any
service that follows the OpenAI style of API (for example a hosted Ollama). Switching requires no
code change.

**Why this priority**: the user wants to compare models and avoid depending on one provider; the
memory in later stories also needs a similarity service.

**Independent Test**: run the same regression messages once with each language model choice and
verify both work and nothing in the tool's behavior other than the model's answers changes. Remove
a key and verify the failure is handled in Portuguese.

**Acceptance Scenarios**:

1. **Given** the configuration selects the Claude service, **When** the user pastes a message,
   **Then** the proposal is produced as in 001.
2. **Given** the configuration selects an OpenAI-style service with its address, model and key,
   **When** the user pastes a message, **Then** the proposal is produced through that service.
3. **Given** a service is not configured or its key is missing, **When** the user pastes a message,
   **Then** they see a clear message in Portuguese, keep their text, and can fill the table by hand,
   exactly as in 001.
4. **Given** a service fails or answers with something unusable, **When** the user pastes a message,
   **Then** the tool retries once and then falls back as in 001.
5. **Given** any configuration, **When** the tool shows data, errors or the history, **Then** no key
   or secret appears there and none is stored in the database.
6. **Given** the similarity service is not configured, **When** the user uses the tool, **Then**
   everything from 001 works and only the memory features of the next stories are inactive.

---

### User Story 3 - Remember the orders the user confirms (Priority: P2)

When the user approves an order, the system remembers the whole message together with its final
approved lines, and each line's written text together with the product the user confirmed. Only
what the user confirmed is remembered, never an unconfirmed suggestion. If the similarity service is
down when the order is approved, the approval still succeeds and the memory is completed later by a
reprocess command. The user can see in the history that an order was remembered.

**Why this priority**: it feeds the two stories that follow, and it must never put an approval at
risk.

**Independent Test**: approve an order and verify its message and lines are remembered and shown as
remembered in the history; approve another with the similarity service down and verify the approval
succeeds, the history shows the memory is pending, and the reprocess command completes it.

**Acceptance Scenarios**:

1. **Given** an order the user approves, **When** the approval finishes, **Then** the message and
   its final approved lines, and each line's written text with its confirmed product, are
   remembered, and the history shows "Memorizado" for that order.
2. **Given** lines the user removed or left unconfirmed, **When** the order is approved, **Then**
   only the user's final confirmed lines are remembered, never the removed lines or unconfirmed
   suggestions.
3. **Given** the similarity service is down, **When** the user approves an order, **Then** the
   approval succeeds, the order is saved normally, and the history shows "Memória pendente".
4. **Given** orders with a pending memory, **When** the user runs the reprocess command with the
   service available, **Then** every pending memory is completed, and running it again changes
   nothing.
5. **Given** the user changed which similarity service or model is configured, **When** old and new
   memories exist, **Then** only memories made with the same model are used for help, and the
   reprocess command can recompute the others.

---

### User Story 4 - Better suggestions while matching (Priority: P2)

During review, lines flagged "revisar" show their candidates reordered using similar lines the user
confirmed before, and may pre-select the most likely one, with the reason shown in Portuguese (for
example "parecido com um pedido anterior"). This never makes a line accepted automatically: the user
must still confirm. Look-alike products such as "Abre Caminho" and "Abre C. da Felicidade" are never
confused because of similarity. If the memory or the similarity service is unavailable, matching
works exactly as in 001.

**Why this priority**: it is the point of the memory for matching, but it must never weaken the
strict matching rules.

**Independent Test**: seed the memory with confirmed lines, paste messages containing new wordings
that resemble them, and verify the flagged lines show the right product first with the reason, are
still pending until confirmed, and that look-alike products are never auto-accepted.

**Acceptance Scenarios**:

1. **Given** a flagged line whose wording resembles a line the user confirmed before, **When** the
   table is shown, **Then** the confirmed product appears among the candidates, is pre-selected, and
   shows the reason "parecido com um pedido anterior".
2. **Given** such a pre-selected line, **When** the user tries to approve without confirming it,
   **Then** approval is blocked exactly as for any flagged line.
3. **Given** a remembered line for "Abre Caminho", **When** a message says "abre caminho da
   felicidade", **Then** the line is never accepted automatically as "Abre Caminho"; it shows
   candidates for confirmation, and "Abre C. da Felicidade" is among them.
4. **Given** a line that matches exactly or through a confirmed phrase, **When** it is processed,
   **Then** it is accepted as in 001 and memory plays no part.
5. **Given** the memory is empty, the similarity service is unavailable, or it is slow, **When** a
   message is processed, **Then** matching behaves exactly as in 001 and nothing is blocked.
6. **Given** the same wording was confirmed for different products at different times, **When** it
   reappears, **Then** the candidates offer both, the most recent first, and the user decides.

---

### User Story 5 - Learn each customer's way of writing (Priority: P3)

When reading a new message, the system uses similar past approved messages as examples, so it reads
each customer's habits better over time. If the memory is unavailable, it reads exactly as in 001.

**Why this priority**: the biggest long-term gain, but only useful once enough orders are remembered.

**Independent Test**: remember a few approved messages in an unusual style, paste a new message in the
same style, and verify the examples used are the similar past messages and that the reading still
goes through the same review; with the memory unavailable, verify the reading is as in 001.

**Acceptance Scenarios**:

1. **Given** past approved messages similar to a new one, **When** the new message is read, **Then**
   up to three of the most similar are used as examples for the reading.
2. **Given** no similar past message, the memory is empty, or the service is unavailable, **When** a
   message is read, **Then** it is read exactly as in 001.
3. **Given** a reading that used examples, **When** the proposal is shown, **Then** it goes through
   the same matching, flags and human approval as any other.

---

### Edge Cases

- First use with an empty memory: everything behaves as in 001.
- The same message approved twice (for example re-pasted): remembered once per approval; neither
  breaks matching.
- A remembered wording whose confirmed product was later corrected by the user: the most recent
  confirmation leads, and the older one stays available as a lower candidate.
- A very long message: remembered whole; if too long for the similarity service, it is shortened for
  the memory only and the stored message stays complete.
- Empty or meaningless lines (for example added by hand with no written text): never remembered.
- The similarity service answers slowly: the review screen is never blocked waiting for memory help
  beyond a short limit, after which matching continues as in 001.
- Two approvals at the same time: each is saved completely or not at all.
- The reprocess command interrupted halfway: running it again finishes the rest without duplicating.
- Configuration changed between runs (different model): memories made with another model are not
  mixed in for help until reprocessed.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The system MUST save every order, line, correction and remembered phrase in one
  database that survives restarts, and MUST NOT keep application data in local files.
- **FR-002**: The system MUST behave for the user exactly as in 001 regarding screens, review,
  approval rules, history and downloads, when the memory features are unused or unavailable.
- **FR-003**: The system MUST refuse to start, with a clear message in Portuguese, when the database
  is not configured or cannot be reached.
- **FR-004**: When the database becomes unreachable while running, the system MUST show a clear
  message in Portuguese, MUST NOT leave any order partly saved, and MUST recover when the database
  returns.
- **FR-005**: The system MUST let the user choose the language model service by configuration only
  (service address, model name, key from the environment), with at least two choices: the current
  Claude service and any OpenAI-style service.
- **FR-006**: The system MUST let the user choose the similarity service by configuration only
  (service address, model name, key from the environment), independently of the language model.
- **FR-007**: Keys and secrets MUST be read only from the environment and MUST NOT appear in
  responses, logs shown to the user, or the database.
- **FR-008**: When a service is not configured, fails, or answers with something unusable, the
  system MUST keep the user's text, show a clear message in Portuguese, retry the language model
  once, and offer an empty table to fill by hand, as in 001.
- **FR-009**: When the user approves an order, the system MUST remember the whole message with its
  final approved lines, and each final line's written text with its confirmed product.
- **FR-010**: The system MUST remember only data the user confirmed: never removed lines, never
  unconfirmed suggestions, never lines without written text.
- **FR-011**: An approval MUST succeed even when the similarity service fails; in that case the
  memory is marked pending and completed later by a reprocess command that can be run repeatedly
  without duplicating anything.
- **FR-012**: The history MUST show, for each order, whether its memory is complete ("Memorizado")
  or pending ("Memória pendente").
- **FR-013**: Each memory entry MUST record which similarity model produced it, and only entries made
  with the currently configured model MUST be used for help.
- **FR-014**: During review, for lines flagged "revisar", the system MUST reorder the candidates
  using similar lines the user confirmed before and MAY pre-select the most likely one, showing the
  reason in Portuguese ("parecido com um pedido anterior").
- **FR-015**: Help from memory MUST NEVER make a line accepted automatically, MUST NOT clear the
  need for the user's confirmation, and MUST NOT change the rules for exact names, confirmed
  phrases, or the safe near-match, including the look-alike family rule.
- **FR-016**: Look-alike products MUST NOT be confused because of similarity: a remembered line for
  one product MUST NOT cause a different look-alike wording to be accepted or pre-confirmed.
- **FR-017**: When reading a new message, the system MUST use up to three similar past approved
  messages as examples; with none available, or with the memory unavailable, it MUST read exactly as
  in 001.
- **FR-018**: If the memory or the similarity service is unavailable or slow, the system MUST
  continue as in 001 without blocking the user beyond a short limit.
- **FR-019**: All new screens, labels, reasons, statuses, errors and messages MUST be in Brazilian
  Portuguese.
- **FR-020**: The system MUST NOT include, in this version: a live WhatsApp connection, voice or
  image input, customer header data or a client store, prices or discounts, a screen to browse or
  edit the memory, or deletion of memory entries.

### Key Entities *(include if feature involves data)*

- **Order data (from 001)**: runs, lines, remembered phrases and the history, now all kept in the one
  database.
- **Remembered message**: a past approved message with its final approved lines, the similarity model
  used, and whether its memory is complete or pending.
- **Remembered line**: the written text of a final approved line with the product the user confirmed,
  the similarity model used, and when it was confirmed.
- **AI service settings**: which language model service and which similarity service are in use
  (address, model name); keys are never part of the data.
- **Memory state of an order**: "Memorizado" or "Memória pendente", shown in the history.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: In 100% of tested approvals made while the similarity service is down or failing, the
  approval succeeds and the order can be downloaded.
- **SC-002**: Across the regression messages and the memory-assisted tests, 0 lines are accepted
  automatically to a wrong product because of memory, and 0 look-alike confusions occur.
- **SC-003**: A phrase confirmed once is matched automatically the next time in 100% of cases, as in
  001, including after a restart.
- **SC-004**: With the memory filled by confirmed orders, the correct product is the first suggestion
  for at least 90% of the flagged regression lines that resemble a confirmed line, against 83% on
  the same lines in 001.
- **SC-005**: In 100% of start attempts without a reachable database, the tool does not start and
  shows a clear message in Portuguese.
- **SC-006**: The regression messages run successfully with each of the two language model choices
  by changing configuration only, with 0 code changes.
- **SC-007**: 0 occurrences of a key or secret in any response, history view, or stored data.
- **SC-008**: All acceptance scenarios of 001 still pass unchanged.
- **SC-009**: After a service outage, the reprocess command completes 100% of the pending memories,
  and running it twice produces no duplicates.
- **SC-010**: 100% of text shown to the user by the new features is in Brazilian Portuguese.

## Assumptions

- The only user is the business owner, running the tool on their own computer; no sign-in or roles.
- The database runs locally at first and is moved to a hosted service later by changing its address
  only; no data from 001's earlier demonstration runs needs to be carried over.
- The similarity service follows the OpenAI style of API, as the language model alternative does; the
  Claude service offers no similarity vectors, so a separate service is needed for the memory.
- The "reprocess command" is run by the user from the command line; a screen for it is not needed.
- Memory help is advisory: it can improve order and pre-selection of candidates but is never
  evidence of identity.
- A short limit for waiting on the similarity service means a few seconds, after which the tool
  continues without memory help.
- The regression messages from 001 are reused, with a small set of confirmed lines added to fill the
  memory for SC-004.
- Details of the exact set of similar lines or messages used (how many, how close) are decided in
  planning and tuned on the regression messages.
