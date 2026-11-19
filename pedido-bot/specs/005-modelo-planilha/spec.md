> **Atualização (2026-11-18):** as rotas do modelo passam a exigir chave com o escopo `modelo` (feature `006-producao-e-acesso`).

# Feature Specification: Modelo de planilha gerenciado

**Feature Branch**: `005-modelo-planilha` (no git repository; folder name only)

**Created**: 2026-11-18

**Status**: Draft

**Input**: User description: "The order-form model (the Excel template, 167 products) becomes managed through the API of the bot, so that the stock system can offer an export button and an import button, and the bot reports model problems. Constitution v2.2.0."

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Export the model (Priority: P1)

A person asks for the model and receives the **active** order form as an Excel file: the same form the bot
fills, with its formulas. They can open it, add new products in free rows and bring it back.

**Why this priority**: it is the starting point for any change of products.

**Independent Test**: request the model, open the file and check it is the form with the 167 products and
its formulas.

**Acceptance Scenarios**:

1. **Given** the system has just been installed, **When** the model is requested, **Then** a file named
   `modelo-pedido.xlsx` arrives with the products of the original form and its formulas intact.
2. **Given** a new model was imported before, **When** the model is requested, **Then** the file is the
   new model, not the original.
3. **Given** the file received, **When** it is opened in Excel, **Then** it opens without repair
   messages.

---

### User Story 2 - Import a new model (Priority: P1)

A person sends a new Excel file. If it is valid, it becomes the active model at once, with no restart: the
products, their order on the form and their exact wordings are rebuilt from it. The answer says how many
products it has and which products were **added**, **removed** or **renamed** compared with the previous
active model. An invalid file is refused with **one** Portuguese message saying what is wrong and asking
to check the model, and the active model stays exactly as it was.

**Why this priority**: it is how new products enter the system.

**Independent Test**: export the model, add a product in a free row, import it, send an order naming the
new product, confirm it and open the Excel returned.

**Acceptance Scenarios**:

1. **Given** the exported model with one new product written in a free row, **When** it is imported,
   **Then** the answer reports that product as added and the next order that names it gets that product.
2. **Given** that order is confirmed, **When** the Excel is opened, **Then** the quantity is in the cell
   of the new product and every formula still works.
3. **Given** the exported model imported again unchanged, **When** the answer arrives, **Then** nothing is
   reported as added, removed or renamed.
4. **Given** a model where a product name was changed or a product deleted, **When** it is imported,
   **Then** the answer lists it as renamed or removed.
5. **Given** a file that is not a readable `.xlsx` (an old `.xls`, a picture, a damaged file), **When** it
   is imported, **Then** it is refused with a message saying to save the model as `.xlsx` and to check it,
   and the active model does not change.
6. **Given** a file larger than the limit (5 MB by default), **When** it is imported, **Then** it is
   refused and the active model does not change.
7. **Given** a model with no product in the expected places, with two products of the same name, or with
   a merged quantity cell, **When** it is imported, **Then** it is refused with one message that says what
   is wrong and to check the model, and the active model does not change.
8. **Given** any import, **When** it finishes, **Then** the previous model is still stored and is never
   deleted.

---

### User Story 3 - The customer is told to check the model when it cannot be used (Priority: P1)

When the model cannot be used, the bot answers the customer with **one short neutral sentence** telling to
check the model, keeps the pending order and invents nothing. This happens (a) when an order arrives and
the active model cannot be read or has no products, and (b) when the customer says ok and a product of the
pending order is no longer in the active model, or its quantity cell is gone. The matching itself does not
change: a written wording is still matched to the closest product of the active model, and the bot still
never reports doubts about wording.

**Why this priority**: the person who maintains the model must find out when it breaks.

**Independent Test**: make an order, import a model without one of its products, say ok and read the
reply; the order must still be pending.

**Acceptance Scenarios**:

1. **Given** an active model that cannot be read or has no products, **When** an order arrives, **Then**
   the reply is one short neutral sentence about checking the model, and nothing is stored as pending.
2. **Given** a pending order and a new model without one of its products, **When** the customer says ok,
   **Then** the reply is one short neutral sentence about checking the model, no file is sent and the
   order stays pending.
3. **Given** that situation, **When** the customer sends a new order, **Then** the new order replaces the
   pending one and works with the new model.
4. **Given** a pending order and a new model that still has all its products, **When** the customer says
   ok, **Then** the Excel is generated with the new model and sent.
5. **Given** a normal order and a normal model, **When** the bot replies, **Then** the reply is exactly
   what it was before this feature.

---

### User Story 4 - Information about the active model (Priority: P2)

A person asks which model is active and receives its version, the file name it came from, the number of
products and when it was activated.

**Why this priority**: it lets the screen show what is in use.

**Independent Test**: ask, import a model, ask again and compare.

**Acceptance Scenarios**:

1. **Given** the original model, **When** the information is requested, **Then** it shows version 1, the
   original file name, 167 products and the activation time.
2. **Given** a new model imported with a file name, **When** the information is requested, **Then** it
   shows the next version, that file name and its number of products.

---

### User Story 5 - Learned nicknames follow the model (Priority: P2)

Each learned nickname remembers the product **name** it was confirmed for. When a new model is activated,
every nickname whose product no longer exists, or whose product name changed, is disabled. Nothing is
deleted. Nicknames from before this feature are filled in from the current model.

**Why this priority**: otherwise a nickname could point to a different product after a change of the
model.

**Independent Test**: learn a nickname, import a model that renames or removes its product, check that it
is disabled and still listed; import the unchanged model and check that it stays active.

**Acceptance Scenarios**:

1. **Given** a nickname for a product that is removed by a new model, **When** the model is activated,
   **Then** the nickname is disabled and still listed.
2. **Given** a nickname for a product that is renamed, **When** the model is activated, **Then** it is
   disabled and still listed.
3. **Given** a nickname for a product that is unchanged, **When** a new model is activated, **Then** it
   stays active.
4. **Given** nicknames stored before this feature, **When** the system starts, **Then** each one receives
   the name of its product from the current model.

---

### Edge Cases

- A new model that adds products in rows where the old one had none: they are found by the next order.
- A new model that moves a product to another row or block: it is the same name in a new position; the
  order of the list follows the new position. Pending orders and nicknames that point to its old position
  are handled by the product name (the name is what links them; see Assumptions).
- Two imports at the same time: they are applied one after the other; the last one is the active one.
- A model with more than 167 products: accepted if valid.
- A file whose name is missing: stored with a default name.
- An empty request body: refused as a file that is not a readable `.xlsx`.
- The database holds no model yet: the original form is installed as version 1.
- A pending order that refers to a product by position that now holds a **different** product name:
  the order is treated as having a product missing.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The system MUST return the active model as an Excel file named `modelo-pedido.xlsx`, with
  its formulas, so it can be edited and imported back.
- **FR-002**: The system MUST accept a new Excel file as the model, validate it and, only if valid, make
  it the active model immediately, without a restart, rebuilding the catalog (products, form order,
  exact wordings, abbreviation variants) from it.
- **FR-003**: A model MUST be refused, with one Portuguese message saying what is wrong and to check the
  model, when: it is not a readable `.xlsx` (an old `.xls` gets a message saying to save it as `.xlsx`);
  it is larger than the limit (5 MB by default, configurable); it has no product in the expected places
  (names in columns C, G, K, O and S of rows 4 to 46, the quantity cell two columns to the left); two
  products have the same normalized name; or a quantity cell is merged.
- **FR-004**: A refused model MUST leave the active model exactly as it was; a model MUST never be
  deleted: every accepted model is stored with its file name, version and activation time.
- **FR-005**: When a model is accepted, the answer MUST give the new version, the file name, the number
  of products and the products added, removed and renamed compared with the previous active model.
- **FR-006**: The original form of the repository MUST be only the seed: it is installed as version 1
  when the database holds no model.
- **FR-007**: The system MUST return the information of the active model: version, file name, number of
  products and activation time.
- **FR-008**: When an order arrives and the active model cannot be read or has no products, the bot MUST
  reply one short neutral sentence telling to check the model, store nothing as pending and keep any
  pending order.
- **FR-009**: When the customer says ok and a product of the pending order is not in the active model
  (or its quantity cell is gone, or the product name at its position is different), the bot MUST reply one
  short neutral sentence telling to check the model, MUST NOT send a file and MUST keep the order pending.
- **FR-010**: A pending order made with the previous model MUST be confirmed with the new one when all its
  products still exist.
- **FR-011**: Matching MUST stay as before: every written wording goes to the closest product of the
  active model, exact wordings first; the bot MUST NOT report doubts about wording.
- **FR-012**: Each learned nickname MUST store the name of the product it was confirmed for; nicknames
  stored before this feature MUST be filled in from the current model.
- **FR-013**: When a model is activated, every nickname whose product no longer exists or whose product
  name changed MUST be disabled and MUST NOT be deleted.
- **FR-014**: Errors of these requests MUST be JSON with a code and a Portuguese message; the replies
  of the bot to customers for normal orders MUST NOT change.
- **FR-015**: All text the user sees MUST be in Brazilian Portuguese.
- **FR-016**: The system MUST NOT include, in this version: a screen in this project, restoring an older
  model through the API, editing products one by one, API keys, or the WhatsApp connection.

### Key Entities *(include if feature involves data)*

- **Model**: an order-form file with its version number, its original file name, when it was activated,
  and whether it is the active one; exactly one is active; none is ever deleted.
- **Product**: an item read from the active model, with its name and its position on the form.
- **Model comparison**: the lists of products added, removed and renamed between the previous active
  model and a new one.
- **Nickname**: as in feature 004, now with the product name it was confirmed for.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: In 100% of tests, after importing a valid model that adds a product, the next order naming
  it lists that product and the Excel has its quantity in the right cell, with no restart.
- **SC-002**: In 100% of tests, an invalid import leaves the active model unchanged and returns exactly
  one Portuguese message saying to check the model.
- **SC-003**: In 100% of tests, exporting the model and importing the same file reports no product as
  added, removed or renamed and keeps every nickname active.
- **SC-004**: In 100% of tests, a removed or renamed product disables its nicknames, and no row is
  deleted.
- **SC-005**: In 100% of tests, a pending order whose product left the model gets the neutral sentence
  about checking the model and stays pending.
- **SC-006**: In 100% of tests, no previous model is ever lost.
- **SC-007**: A person can export, edit and import a model in under 2 minutes of the system's own time
  (each request answers in under 3 seconds for a model of 200 products).
- **SC-008**: The replies of the bot for normal orders are unchanged, and every test of the earlier
  features still passes.

## Assumptions

- The link between a pending order or a nickname and a product is the **position** (block and row) **plus
  the product name**; if the name at that position changed, the product counts as removed.
- The size limit of a model is 5 MB by default and can be changed by configuration.
- Only `.xlsx` is accepted; an old `.xls` must be saved as `.xlsx` first.
- There is no sign-in: anyone who can reach the system can export and import the model. Protection comes
  from keeping every previous model, so a wrong model can be restored by hand from the database.
- The screen that uses these requests is a separate feature of the stock system.
- The catalog, the matching, the memory and the conversation of earlier features are reused.
