> **Aviso (2026-11-16):** esta especificação foi substituída em parte pela feature `003-bot-whatsapp-simples` (bot simples: lista, ok/não, sem tela de revisão, sem memória RAG). Vale o que está em `specs/003-bot-whatsapp-simples/`.

# Feature Specification: Pedido a partir de mensagem de WhatsApp (intake → Excel)

**Feature Branch**: `001-pedido-intake-excel` (no git repository; name used for the spec folder only)

**Created**: 2026-10-23

**Status**: Draft

**Input**: User description: "Sub-project 1 (intake → Excel) per docs/superpowers/specs/2026-10-23-pedido-whatsapp-excel-design.md: a local pt-BR tool where the user pastes a customer's WhatsApp order text, the system extracts the items, matches them strictly to the ~167-product catalog from the order form, flags uncertain lines, lets the user review and approve, then fills the order form with quantities in dozens and per-category total dozens, and saves runs and corrections so they can later be learned from."

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Turn a pasted message into a reviewed order (Priority: P1)

The user receives a customer's order on WhatsApp, written informally ("2 dz abre caminho, meia
dúzia de arruda, 3 dz de sao jorge"). They paste the text into the tool, see a proposed order as
an editable table of products and quantities in dozens, fix anything wrong, and approve it.

**Why this priority**: this is the whole point of the tool. Without it nothing else has value, and
on its own it already replaces retyping orders by hand.

**Independent Test**: paste a message with several items; verify a proposed table appears with
the right products and quantities, that unclear lines are marked, and that the user can edit and
approve it.

**Acceptance Scenarios**:

1. **Given** a pasted message listing clearly written products and quantities, **When** the user
   submits it, **Then** a table is shown with each product matched to its catalog entry and its
   quantity in dozens.
2. **Given** a message that says "meia dúzia", **When** it is processed, **Then** the quantity is
   0.5 dozen.
3. **Given** a line the system cannot match with certainty, **When** the table is shown, **Then**
   that line is marked "revisar", shows up to three candidate products, and nothing is chosen
   silently.
4. **Given** a table with an unresolved line (no product chosen, invalid quantity, two lines for the same
   product, or a "revisar" line the user has not confirmed), **When** the user tries to approve,
   **Then** approval is blocked and the unresolved lines are highlighted.
5. **Given** the user edits a product, edits a quantity, removes a line, or adds a line, **When**
   they approve, **Then** the approved order reflects exactly their final table.
6. **Given** a "revisar" line that already shows a suggested product, **When** the user has not
   confirmed or changed it, **Then** the line still counts as unresolved and approval is blocked until
   they explicitly confirm it.
7. **Given** two lines for the same product, **When** the user chooses to merge them, **Then** one
   line remains with the quantities added together and the duplicate block is cleared.
8. **Given** a message with no recognizable order, **When** it is processed, **Then** an empty table
   is shown with a clear Portuguese note that nothing was recognized.

---

### User Story 2 - Get the filled order form (Priority: P1)

After approving, the user downloads the company's order form with the approved quantities written
into the correct product cells, plus per-category totals of dozens for conferring.

**Why this priority**: the order form is the deliverable the business actually uses; a reviewed
table with no form to send on does not finish the job.

**Independent Test**: approve a known order and open the downloaded file; verify each quantity is in
the cell of the right product and the total dozens per category matches the table.

**Acceptance Scenarios**:

1. **Given** an approved order, **When** the user requests the file, **Then** a filled copy of the
   order form is delivered with each quantity next to the correct product.
2. **Given** an approved order, **When** the file is produced, **Then** the total dozens per
   category (Incensos, Defumadores, Def/Inc) are shown to the user and agree with the sum of the
   approved lines.
3. **Given** any order, **When** the form is filled, **Then** the original blank order form is never
   changed, and the header (customer, address, payment terms, etc.) is left blank.

---

### User Story 3 - Never confuse similar products (Priority: P1)

Many products differ by one word ("Abre Caminho", "Abre C. da Felicidade", "Abre C. do Dinheiro").
The system must never silently pick the wrong one of a look-alike family.

**Why this priority**: a wrong product in a wholesale order costs money and trust; this rule shapes
how every other part behaves, so it ships with the first working version.

**Independent Test**: run messages containing each look-alike product, abbreviations, and typos
inside the same family; verify exact names resolve correctly and ambiguous ones are flagged, never
auto-accepted to the wrong product.

**Acceptance Scenarios**:

1. **Given** the text "abre caminho", **When** processed, **Then** it matches "Abre Caminho" and
   not any other "Abre …" product.
2. **Given** the text "abre c. da felicidade", **When** processed, **Then** it matches "Abre C. da
   Felicidade" and not "Abre Caminho".
3. **Given** a misspelling inside a look-alike family (e.g., "abre camino"), **When** processed,
   **Then** the line is flagged for review with candidates and is not accepted automatically.
4. **Given** a product name the system has never seen but that is almost identical to exactly one
   unique product, **When** the match is very close and clearly ahead of every other candidate,
   **Then** it may be accepted automatically; otherwise it is flagged.

---

### User Story 4 - The system remembers my corrections (Priority: P2)

When the user confirms or corrects which product a written phrase means, the system remembers that
phrase so the same wording is recognized immediately next time. Every processed message is kept
with what the system suggested next to what the user finally approved.

**Why this priority**: it makes review shrink over time and is the foundation for the later learning
sub-project, but the tool is useful without it on day one.

**Independent Test**: correct a line, approve, then paste a message with the same wording; verify
the line is now matched without review. Check the saved history shows suggestion and final answer
side by side.

**Acceptance Scenarios**:

1. **Given** the user corrected "abre c felicidade" to the right product and approved, **When** a
   later message uses the same wording, **Then** it is matched automatically.
2. **Given** a processed message, **When** the user opens the history, **Then** each line shows what
   was suggested, with what confidence, and what was finally approved.

---

### User Story 5 - Failures never lose my work (Priority: P2)

If the text analysis service is unavailable or returns something unusable, the user keeps their
pasted message and can retry or fill the table by hand.

**Why this priority**: protects trust in daily use, but only matters once the core flow works.

**Independent Test**: simulate a failed analysis; verify a clear Portuguese message, the pasted text
is preserved, and an empty editable table is offered.

**Acceptance Scenarios**:

1. **Given** the analysis cannot be completed, **When** the user submits, **Then** a clear message in
   Portuguese appears, their text is kept, and they can retry.
2. **Given** an unusable analysis result after one retry, **When** shown, **Then** the original
   message is displayed beside an empty table the user can fill manually.
3. **Given** the form cannot be produced, **When** the user requests it, **Then** a clear message in
   Portuguese appears and the approved order stays saved so it can be exported again.

---

### Edge Cases

- A message with the same product written twice (or under two spellings): flagged as a duplicate; the
  user must merge the lines (quantities are added together) before approving; never counted twice
  silently.
- Quantities that are zero, negative, or not a multiple of half a dozen: flagged for review.
- Quantities written in units other than dozens (e.g., "36 unidades"): flagged, since v1 handles
  dozens only.
- A message with no recognizable order at all: shown as an empty table with a clear Portuguese note.
- Products named in the message that are not in the catalog: flagged as unmatched, never dropped.
- A very long message or many items at once: all lines are processed and reviewable.
- Accents, capital letters, punctuation, and spacing differences in product names: do not prevent
  an exact match.
- Messages in a mix of abbreviations, e.g., "C." for Caminho, "Def." for Defumador: understood
  according to the catalog's own abbreviations.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The system MUST let the user paste the text of one customer message and submit it for
  analysis.
- **FR-002**: The system MUST turn the message into a list of proposed order lines, each with a
  written product name, a quantity, and a unit, understanding informal quantities such as "meia
  dúzia" (0.5 dozen).
- **FR-003**: The system MUST match each line against the catalog of products taken from the
  company's order form, and show for each line the proposed product and how certain the system is.
- **FR-004**: The system MUST automatically accept a match only when the normalized text equals a
  catalog name or a previously remembered phrase exactly, or when a close match is very high, clearly
  ahead of the runner-up, and not part of a look-alike family.
- **FR-005**: The system MUST flag every other line "revisar", showing up to three candidate
  products, and MUST NEVER silently choose a product for a flagged line. A suggested product shown on a flagged
  line is not a choice until the user explicitly confirms or changes it.
- **FR-006**: The system MUST NEVER auto-accept a match among products that share their first word
  (look-alike families such as "Abre …") unless the text is an exact name or remembered phrase.
- **FR-007**: The system MUST flag lines that are unmatched, low certainty, have a quantity that is
  not positive or not a multiple of half a dozen, are in a unit other than dozens, or duplicate
  another line's product. No line may be dropped silently.
- **FR-008**: The system MUST show the total dozens per category (Incensos, Defumadores, Def/Inc) so
  the user can check them against the message.
- **FR-009**: The user MUST be able to change a line's product (by searching the catalog), change its
  quantity, remove a line, and add a line before approving.
- **FR-010**: The system MUST block approval while any line is unresolved and MUST highlight those lines. A line is
  unresolved when it has no product, has an invalid quantity, duplicates another line's product, or is
  flagged "revisar" and has not been explicitly confirmed or changed by the user.
- **FR-011**: The system MUST NOT produce the filled order form until the user explicitly approves
  the reviewed order.
- **FR-012**: On approval, the system MUST deliver a copy of the order form with each approved
  quantity written next to the correct product, and MUST leave the original form untouched.
- **FR-013**: The delivered form MUST leave the header fields (date, customer name, address, city,
  state, payment terms, carrier) blank in this version.
- **FR-014**: When the user confirms or corrects a line's product, the system MUST remember the
  written phrase for that product so the same wording is matched automatically in later messages. Lines the system accepted
  automatically and the user left unchanged are not remembered.
- **FR-015**: The system MUST save every processed message with, for each line, the original text,
  the extracted quantity, the suggested product and certainty, and the user's final product and
  quantity, so suggestion and final answer can be compared.
- **FR-016**: All screens, labels, flags, validation messages, error messages, and the text the
  system produces for the user MUST be in Brazilian Portuguese.
- **FR-017**: If analysis fails or returns unusable results, the system MUST keep the user's pasted
  text, show a clear Portuguese message, allow a retry, and offer an empty table to fill manually.
- **FR-018**: If the form cannot be produced, the system MUST show a clear Portuguese message and
  keep the approved order saved so it can be exported again.
- **FR-019**: The system MUST NOT include, in this version: a live WhatsApp connection, voice or image
  input, customer header data or a client store, prices or discounts, or similarity search over past
  messages.

### Key Entities *(include if feature involves data)*

- **Product**: an item of the company's catalog, with a name, a category (Incensos, Defumadores,
  Def/Inc), and its position on the order form.
- **Remembered phrase (alias)**: a written way of naming a product that the user has confirmed, tied
  to exactly one product.
- **Message run**: one pasted message, with when it was processed and when (if ever) it was approved.
- **Run line**: one line of a run, holding the written text, the extracted quantity, the suggested
  product with its certainty, the user's final product, and the final quantity.
- **Order form**: the company's blank form (never modified) and the filled copy produced from an
  approved run.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: On a set of about 20 representative sample messages written in Portuguese (informal,
  abbreviated, with typos and "meia dúzia"), at least 90% of lines are correct without any user edit.
- **SC-002**: Across the same sample set, no line is ever accepted automatically to a wrong product,
  and 100% of uncertain lines are flagged for review.
- **SC-003**: A typical order of about 10 items goes from pasted text to a downloaded filled form in
  under 3 minutes, including review.
- **SC-004**: In 100% of approved orders, every quantity in the delivered form sits next to the
  correct product and the category totals match the approved lines.
- **SC-005**: After a correction is approved, the same phrase is matched without review in 100% of
  later messages.
- **SC-006**: 100% of text shown to the user and 100% of generated content is in Brazilian
  Portuguese.
- **SC-007**: A failure in analysis or in producing the form never loses the user's pasted message or
  approved order.

## Assumptions

- The only user is the business owner, using the tool on their own computer; no sign-in, roles, or
  data-protection requirements are in scope for this version.
- One customer message is processed at a time.
- The order form's product names are the complete catalog; there is no separate product list file.
- The header and client data store, prices and discounts, the live WhatsApp connection, voice and
  image input, and similarity search over past messages are deferred to later sub-projects.
- Quantities are always in dozens; other units are flagged, not converted.
- The company's original order form is kept as provided and used as a read-only source.
- Details of how the form's cells and footer totals behave still have to be confirmed against a
  converted copy of the form during planning.
