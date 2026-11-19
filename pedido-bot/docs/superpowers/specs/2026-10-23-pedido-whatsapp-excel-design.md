# Pedido WhatsApp → Excel — Design (Sub-project 1: Intake → Excel)

> **Atualização (feature 002):** o armazenamento deste projeto mudou de SQLite para **Postgres com pgvector** (schema `pedido`, `DATABASE_URL` obrigatória). Onde este documento falar de SQLite ou `data/pedido.db`, vale o que está em `specs/002-rag-memory-providers/`. O restante continua válido.


Date: 2026-10-23
Status: Draft, awaiting user review

## 1. Purpose

A small, internal tool for the user's own wholesale job. A customer sends an order as free-form
WhatsApp text; the tool turns it into a proposed order, lets the user review and correct it, and
produces the filled Excel order form. Corrections are stored so the system can later learn from them.

Everything user-facing is in **Brazilian Portuguese (pt-BR)**: UI, prompts, flags, error messages,
and the language of extracted data. This is a hard requirement.

### Decomposition

The original idea is split into two sub-projects, each with its own spec → plan → build cycle:

1. **Intake → Excel (this spec):** pasted message → chain → reviewed order → filled `.xlsx`.
2. **Learning flow (later):** training messages, RAG over past runs and corrections, accuracy tracking.
   Sub-project 1 stores the data it needs; it does not implement it.

## 2. Confirmed scope (v1)

In scope:
- Input: **pasted text only**, one message per run.
- Fill **product quantities** (in dozens) into the order template.
- Per-category **total dozens**, computed as a sanity check shown to the reviewer.
- Simple **local web page** (pt-BR) to paste, review/edit, approve, download.
- Persist every run and the user's corrections.

Out of scope (recorded so they are not lost):
- Live WhatsApp connection; voice notes; images/handwritten lists.
- Customer header fields (Razão Social, Endereço, Cidade, Estado, Prazo de Pagamento, Transp., Data)
  and a client data store — deferred; the header is left blank in v1.
- Prices, discounts, subtotals/totals in money, "Total de Caixas" — the sheet's own formulas, if any,
  are untouched.
- Vector RAG over past messages (sub-project 2).

## 3. The template (facts read from `PLANILHA 2024.xls`, sheet "Plan1")

- Title "PEDIDO"; ~167 product names in a grid of five column blocks (4 columns per block:
  quantity, unit `dz`, product name, value column).
- Unit is always **dozens (`dz`)**.
- Footer blocks per category: Incensos, Defumadores, Def/Inc (subtotal, discount, total, total dozens).
- Product names are abbreviated and many share prefixes ("Abre Caminho", "Abre C. da Felicidade",
  "Abre C. do Dinheiro", ...). This drives the matching rules in §5.
- The catalog (names + grid position + category) is **derived from the template**; there is no
  separate product list file.
- The template is converted **once to `.xlsx`** (LibreOffice) and that file is filled. The delivered
  file is `.xlsx`. The original `.xls` is kept untouched as source.

Open item for implementation: the "value column" next to each name and the footer formulas could not
be inspected from `.xls` values alone; the converted `.xlsx` must be inspected before writing the
exporter, and any formulas preserved.

## 4. Architecture

- **Python + FastAPI**; one pt-BR page and a few JSON endpoints.
- **SQLite** (single file).
- **LangChain LCEL Runnables.** Deterministic stages are plain functions wrapped in `RunnableLambda`
  so they are unit-testable without the network.
- **Claude API** used only in `extract` and in the ambiguous-match tie-break.

### Modules (one purpose each)

| Module | Responsibility | Depends on |
|---|---|---|
| `catalog` | Load products from the converted template into SQLite with category and grid position (row, block); build the abbreviation list | template file |
| `extract` | Message → raw lines `{texto, quantidade, unidade}`; normalizes "meia dúzia" = 0.5 etc. | Claude API |
| `match` | One raw line → product + confidence + candidates (see §5) | catalog, aliases, (Claude API for tie-break) |
| `validate` | Flags problems, computes total dozens per category | catalog |
| `export` | Writes approved quantities into the template's cells, returns `.xlsx` | catalog, template |
| `store` | Persist runs, lines, corrections, aliases | SQLite |
| `web` | Paste, editable review table, approve, download | all of the above |

## 5. Pipeline

### Chain 1 — proposal (on paste)

```
extract | match.map() | validate
```

`match.map()` runs once per extracted line, in parallel.

### Review (human, in the web table)

Edit product (searchable dropdown), edit quantity, delete or add a line, then **Approve**.
Flagged lines are visually marked; approval is blocked while any line is unresolved
(no product selected or quantity invalid).

### Chain 2 — export (on approve)

```
save_corrections | fill_template
```

## 6. Matching rules (critical)

Many products differ by a single word ("Abre Caminho" vs "Abre C. da Felicidade"), so a high text
similarity does **not** imply the same product. Rules, in order:

1. **Normalize:** lowercase, strip accents and punctuation, collapse whitespace, expand the
   catalog's abbreviations (`C.` → Caminho, `T.` → Todos, `Def.` → Defumador, ...; list derived
   from the catalog and reviewed by the user).
2. **Exact / alias match → auto-accept.** Normalized text equals a normalized catalog name or a
   saved alias exactly.
3. **Safe fuzzy → auto-accept only if ALL hold:**
   - similarity score ≥ configured high threshold (initial: 95/100), and
   - lead over the runner-up ≥ configured margin (initial: 10 points), and
   - **sibling guard passes:** no other catalog product within 15 points of the top score shares the
     first word with it. (So the "Abre …" family can never auto-accept on fuzzy alone.)
4. Otherwise the line is **flagged "revisar"** with the top 3 candidates.
5. **LLM tie-break** (only when candidates are ambiguous) may *pre-select* a candidate in the review
   table but **never** auto-accepts it.
6. **Confirming or correcting a match saves an alias** (normalized text → product), so the same
   wording is an exact match next time.

Thresholds are configuration, tuned against the regression set (§9).

## 7. Validation rules

Flag (never silently drop) any line that is: unmatched; matched with confidence below threshold;
quantity ≤ 0 or not a multiple of 0.5; or a duplicate of another line's product (offer to merge).
Compute and display total dozens per category (Incensos, Defumadores, Def/Inc) for the reviewer to
compare against what the customer wrote.

## 8. Data model

- `catalog(id, nome, categoria, linha, bloco)`
- `aliases(texto_normalizado PRIMARY KEY, produto_id, origem)` — `origem` ∈ {seed, correcao}
- `runs(id, mensagem, criado_em, aprovado_em)`
- `run_lines(run_id, texto, qtd_extraida, produto_sugerido, confianca, produto_final, qtd_final)`

Suggestion and final answer are stored side by side on purpose; this is what sub-project 2 trains on.

## 9. Error handling

- LLM call fails or times out: show a pt-BR error, keep the pasted text, allow retry; never lose input.
- Unparseable extraction output: one retry, then show the raw message with an empty review table to
  fill manually.
- Export failure: show a pt-BR error; the approved run stays saved and can be re-exported.

## 10. Testing

**Test-first (required):** tests are written **before** the code they cover, and must be seen to
fail first (red → green → refactor). For each module in §4 the order is: write its tests from the
rules in §6–§7, run them and confirm they fail for the right reason, then implement. The regression
message set below and the `match` / `validate` / `export` tests are therefore authored before any
implementation of those modules, and the plan's tasks must list the test task ahead of its
implementation task.

- **Unit (no network):** `match`, `validate`, `export`, abbreviation expansion. Examples that must
  hold: "2 dz de Abre Caminho" → that product's quantity cell; "Abre C. da Felicidade" resolves to
  its own entry and **never** to "Abre Caminho"; a typo inside the "Abre …" family is flagged, not
  auto-accepted.
- **Template check:** read the produced `.xlsx` back and compare against the catalog so the
  product → cell mapping cannot drift.
- **LLM stages:** stubbed with canned responses in CI. A regression set of ~20 synthetic pt-BR
  messages (abbreviations, "meia dúzia", several items per line, typos) is run against the stubbed
  and, manually, the real API.

## 11. Success criteria (v1)

- On the synthetic set, the large majority of lines are correct without edits, **zero** lines are
  auto-accepted to a wrong product, and every uncertain line is flagged.
- The filled `.xlsx` opens in Excel with correct dozens in the correct cells.
- All UI text and generated data is pt-BR.

## 12. Handoff to sub-project 2

v1's tables and alias writes are the contract. Sub-project 2 adds retrieval of similar past
messages and corrections, plus accuracy tracking, without changing v1's schema.
