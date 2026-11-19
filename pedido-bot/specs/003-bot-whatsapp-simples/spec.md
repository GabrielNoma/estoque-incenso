> **Atualização (2026-11-16):** estendida pela feature `004-memoria-e-guardrails` (memória silenciosa de apelidos e guardrails do modelo). O que o cliente vê não muda.

# Feature Specification: Bot de pedidos simples (estilo WhatsApp)

**Feature Branch**: `003-bot-whatsapp-simples` (no git repository; folder name only)

**Created**: 2026-11-16

**Status**: Draft

**Input**: User description: "A simple WhatsApp-style order bot: the customer sends an order as free text; the bot matches every item to the closest product, sums repeated products, and replies with only the list in the Excel order followed by \"ok ou não?\"; on ok it generates and sends the Excel; on não the pending order is discarded. The customer is the only reviewer. This feature replaces the review-screen flow of 001 and 002; the conversation is channel-agnostic and is tested through a simple chat page, a real WhatsApp connection being the next feature."

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Receive the organized list of the order (Priority: P1)

The customer writes the order the way they always do ("2 dz abre caminho, meia dúzia de arruda, 3 dz
sao jorge, mais 1 dz são jorge"). The bot answers with **only** the organized list: each product
once, in the order of the Excel form, with the quantity in dozens, and the last line asking "ok ou
não?". Every item is matched to the closest product of the catalog; items of the same product are
summed. The bot never asks a question, never says that something is doubtful or wrong, and never
marks an approximate match.

**Why this priority**: it is the whole point of the bot; with this alone the customer already sees
their order organized.

**Independent Test**: send a message with several items, repeated products, abbreviations and typos;
verify the reply is only the list in form order with summed quantities and the closing line.

**Acceptance Scenarios**:

1. **Given** a message with several items, **When** the bot replies, **Then** the reply contains one
   line per product in the format `<Produto> — <quantidade> dz`, in the order of the Excel form, and a
   final line `ok ou não?`, and nothing else.
2. **Given** "2 dz são jorge" and "1 dz sao jorge" in the same message, **When** the bot replies,
   **Then** São Jorge appears once with 3 dz.
3. **Given** "meia dúzia de arruda", **When** the bot replies, **Then** the line shows `0,5 dz`.
4. **Given** the wording "abre camino" (a typo), **When** the bot replies, **Then** the line shows
   the closest product, "Abre Caminho", with no remark about the typo.
5. **Given** an exact wording of a product (a catalog name, an abbreviation such as "abre c. da
   felicidade", a full wording of "S." as santo, santa or saúde, or "7" written as "sete"), **When**
   the bot replies, **Then** it is matched to that exact product and never to a different one that
   merely looks similar.
6. **Given** a text that resembles nothing in the catalog, **When** the bot replies, **Then** it is
   still matched to the closest product and the reply keeps the same format.

---

### User Story 2 - Confirm with "ok" and receive the Excel (Priority: P1)

After reading the list, the customer answers "ok". The bot then generates the Excel order form with the
quantities written in the right cells and sends it back as a file. Nothing is generated or sent before
the customer says ok.

**Why this priority**: the Excel is the deliverable the business uses.

**Independent Test**: send an order, answer "ok", and open the returned file: each quantity must sit
beside the right product, the prices and totals must calculate, and the header must stay blank.

**Acceptance Scenarios**:

1. **Given** an order waiting for an answer, **When** the customer replies ok (also sim, confirmo,
   isso, certo or blz, in any case and with or without accents or punctuation), **Then** the bot sends
   the Excel file with a one-sentence confirmation.
2. **Given** the file, **When** it is opened, **Then** each quantity is in the cell of its product, the
   formulas of the form still work, the header fields are blank and the original form was not changed.
3. **Given** an order that was not yet confirmed, **When** time passes or other messages arrive, **Then**
   no file is generated or sent.
4. **Given** the file sent, **When** the same order is looked at later, **Then** its list is exactly the
   list the customer confirmed.

---

### User Story 3 - Say "não" or send something else (Priority: P2)

If the customer answers "não", the pending order is discarded and the bot replies with one short
sentence inviting the customer to send the order again. If the customer sends any other text while an
order is waiting, it is read as a **new** order that replaces the pending one, and the bot replies
with the new list.

**Why this priority**: it is how the customer corrects anything, without menus or questions.

**Independent Test**: send an order, answer "não" and check the invitation; send an order and then
another one, answer "ok" and check that the file has only the second order.

**Acceptance Scenarios**:

1. **Given** a pending order, **When** the customer replies não (also nao, n, cancelar or errado),
   **Then** the order is discarded and the bot replies with one short sentence inviting a new order.
2. **Given** a pending order, **When** the customer sends a new order text, **Then** the bot replies
   with the new list and the previous order can no longer be confirmed.
3. **Given** no pending order, **When** the customer sends "ok", **Then** the bot replies with one
   short neutral sentence inviting the customer to send the order, and no file is sent.
4. **Given** a confirmed order, **When** the customer sends "ok" again, **Then** no second file is
   generated; the bot replies as with no pending order.

---

### User Story 4 - The pending order survives a restart (Priority: P2)

Orders and conversations are stored per phone number. If the system is restarted between the list and
the "ok", the "ok" still works. The system refuses to start, with a clear message in Portuguese, if the
database is not configured or cannot be reached.

**Why this priority**: a conversation has state; losing the list would make "ok" meaningless.

**Independent Test**: send an order, restart the system, answer "ok" and receive the Excel; start it
without a database and read the refusal.

**Acceptance Scenarios**:

1. **Given** a pending order, **When** the system is restarted and the customer replies ok, **Then** the
   Excel is sent.
2. **Given** two customers with different phone numbers, **When** both have pending orders, **Then**
   each "ok" confirms only that customer's order.
3. **Given** no database configured, **When** the system is started, **Then** it does not start and
   shows a clear message in Portuguese saying what is missing.
4. **Given** a configured address that cannot be reached, **When** the system is started, **Then** it
   does not start and shows a clear message in Portuguese.
5. **Given** any conversation, **When** it ends, **Then** nothing was written to local files other than
   the file delivered to the customer.

---

### User Story 5 - Failures are short and neutral (Priority: P2)

If the language model is not configured or fails, if the Excel cannot be generated, or if the database
fails, the bot replies with **one short neutral sentence** that tells the customer what to do next, such
as sending the message again in a moment. The pending order is never lost and nothing breaks. A message
with no order in it also gets one short neutral sentence.

**Why this priority**: the bot must stay predictable when a service is down.

**Independent Test**: with the language model switched off, send an order and read the reply; with the
file generation failing, answer "ok" and check that the order is still pending and a retry works.

**Acceptance Scenarios**:

1. **Given** the language model is not configured or does not answer, **When** the customer sends an
   order, **Then** the bot replies with one short neutral sentence asking to send it again in a moment,
   and any previous pending order is kept.
2. **Given** the file cannot be generated, **When** the customer replies ok, **Then** the bot replies
   with one short neutral sentence asking to reply ok again, the order stays pending, and a later ok
   sends the file.
3. **Given** a message that contains no items, **When** the bot replies, **Then** it is one short
   neutral sentence asking to send the order, and the pending order is kept.
4. **Given** the database fails during a conversation, **When** the customer writes, **Then** the bot
   replies with one short neutral sentence and no order is left half-saved.

---

### User Story 6 - A very simple chat page to test (Priority: P2)

A page in Portuguese lets the person testing play the customer: a field for the phone number, the
conversation as chat bubbles, a message box and a send button. When the bot returns the Excel, the page
shows it as a download link.

**Why this priority**: it is how the flow is tried before the real WhatsApp connection exists.

**Independent Test**: open the page, chat through a full order and download the file.

**Acceptance Scenarios**:

1. **Given** the page, **When** the person types a phone number and a message and sends, **Then** the
   message and the bot's reply appear as bubbles.
2. **Given** the bot returns the Excel, **When** it is shown, **Then** it appears as a download link.
3. **Given** a reload of the page, **When** the same phone number is used, **Then** the pending order
   can still be confirmed.

---

### Edge Cases

- A message with the same product written in several ways: summed into one line.
- An item written without a quantity: counted as 1 dozen.
- Quantities of zero or negative: ignored; items in units are converted to dozens by the reading step.
- A very long message or many items: all are listed.
- An empty message: one short neutral sentence inviting an order.
- A reply such as "OK!", "Ok.", "SIM" or "não" with accents or punctuation: understood.
- Two customers writing at the same time: each conversation is separate by phone number.
- The same wording of two catalog products when an abbreviation is ambiguous: an exact wording always
  identifies a single product.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The system MUST read the customer's free-text order and extract each item with its written
  name and a quantity in dozens, understanding informal quantities such as "meia dúzia".
- **FR-002**: The system MUST match every item to the closest product of the catalog, with no minimum
  similarity, and MUST NOT ask questions, mark approximations or report doubts to the customer.
- **FR-003**: An exact wording of a product (catalog name, abbreviation expansions, full wordings of an
  ambiguous abbreviation, "7" written as "sete") MUST always win over an approximate match; ties
  between equally close products MUST be resolved by the Excel order.
- **FR-004**: The system MUST sum the quantities of items that match the same product.
- **FR-005**: The reply to an order MUST be only the list and its closing line: one line per product in
  the form `<Produto> — <quantidade> dz`, in the Excel order (block by block, top to bottom), with
  quantities written with a comma for decimals and no trailing zeros, followed by the line `ok ou não?`.
- **FR-006**: Nothing MUST be generated or sent as a file before the customer replies ok.
- **FR-007**: When the customer replies ok (ok, sim, confirmo, isso, certo, blz; case, accents and
  punctuation ignored), the system MUST generate the Excel order form with the confirmed quantities in
  the right cells, preserving the form's formulas, leaving the header blank and not changing the
  original form, and MUST send it to the customer with a one-sentence confirmation.
- **FR-008**: When the customer replies não (não, nao, n, cancelar, errado), the system MUST discard
  the pending order and reply with one short sentence inviting the customer to send the order again.
- **FR-009**: Any other text sent while an order is pending MUST be read as a new order that replaces
  the pending one.
- **FR-010**: "ok" or "não" with no pending order, and a message with no items, MUST get one short
  neutral sentence inviting the customer to send the order, and no file.
- **FR-011**: A confirmed order MUST NOT generate a second file when "ok" is sent again.
- **FR-012**: The system MUST store, per phone number, each order message, the list sent, the customer's
  answer and the state of the order (waiting, confirmed, refused, replaced), so a pending order survives
  a restart; conversations of different phone numbers MUST NOT interfere.
- **FR-013**: The system MUST refuse to start, with a clear message in Portuguese, when the database is
  not configured or cannot be reached, and MUST NOT store application data in local files.
- **FR-014**: When the language model fails or is not configured, when the file cannot be generated, or
  when the database fails, the system MUST reply with one short neutral Portuguese sentence telling the
  customer what to do next, MUST keep the pending order, and MUST NOT leave an order half-saved.
- **FR-015**: The language model MUST be configurable by configuration only (service address, model
  name, key from the environment), with at least two choices: the current Claude service and any
  OpenAI-compatible service; keys MUST NOT appear in replies or stored data.
- **FR-016**: The system MUST provide a very simple chat page in Portuguese with a phone number field,
  chat bubbles, a message box and a send button, showing the Excel as a download link.
- **FR-017**: Everything the customer sees MUST be in Brazilian Portuguese.
- **FR-018**: The conversation MUST be independent of the channel: it receives a phone number and a text
  and returns a reply text and optionally a file, so a real WhatsApp connection can use it later.
- **FR-019**: The system MUST NOT include, in this version: a real WhatsApp connection, voice or image
  input, customer header data or a client store, prices or discounts, learned aliases, a vector memory or
  any owner review screen.

### Key Entities *(include if feature involves data)*

- **Product**: an item of the company's catalog, with its name, its category and its position on the
  order form.
- **Order**: what one customer asked in one message, with the list of products and quantities sent back,
  the customer's answer, and its state (waiting, confirmed, refused, replaced).
- **Conversation**: the sequence of orders of one phone number; at most one order is waiting for an
  answer at a time.
- **Order file**: the Excel form generated from a confirmed order.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: In 100% of order messages the bot's reply is exactly the list followed by `ok ou não?`,
  with no question, remark or marker.
- **SC-002**: In 100% of cases items of the same product are summed into one line, and the list follows
  the Excel order.
- **SC-003**: In 100% of cases no file is generated or sent before the customer replies ok.
- **SC-004**: In 100% of cases an exact wording of a product is matched to that product.
- **SC-005**: At least 90% of the lines of the regression messages end up on the intended product.
- **SC-006**: A pending order survives a restart in 100% of tests, and each customer's ok confirms only
  that customer's order.
- **SC-007**: In 100% of the start attempts without a reachable database the system does not start and
  shows a clear Portuguese message.
- **SC-008**: In 100% of the failure tests the bot replies with a single short neutral sentence and the
  pending order is kept.
- **SC-009**: The Excel file of a confirmed order has every quantity in the cell of its product, the
  form's formulas intact, a blank header, and the original form unchanged, in 100% of tests.
- **SC-010**: 100% of the text the customer sees is in Brazilian Portuguese, and the bot never asks
  anything other than "ok ou não?".

## Assumptions

- The customer is identified only by the phone number; no sign-in, no name, no address.
- The Excel is delivered in the same conversation to the customer who confirmed the order.
- The "Excel order" is the order of the form: the first block of columns from top to bottom, then the
  second block, and so on.
- An item written without a quantity counts as one dozen.
- The first version is tested through the chat page; the real WhatsApp connection is the next feature
  and will reuse the same conversation.
- Matching the closest product whatever the similarity is a deliberate decision of the owner: the
  customer reading the official product names is the only check.
- The language model's job is only to read the items; everything else is fixed rules.
- The catalog, the order form template and the Excel filling already exist from the earlier features and
  are reused unchanged.
