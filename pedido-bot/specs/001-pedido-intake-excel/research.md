# Research: Pedido a partir de mensagem de WhatsApp (intake → Excel)

> **Atualização (feature 002):** o armazenamento deste projeto mudou de SQLite para **Postgres com pgvector** (schema `pedido`, `DATABASE_URL` obrigatória). Onde este documento falar de SQLite ou `data/pedido.db`, vale o que está em `specs/002-rag-memory-providers/`. O restante continua válido.


All items from the Technical Context are resolved. There are no open `NEEDS CLARIFICATION` items;
the two assumptions listed at the end are both confirmed.

## Findings about the template (measured, not assumed)

Read from `PLANILHA 2024.xls` (sheet "Plan1") with `xlrd` and a raw read of the binary (BIFF) records:

- 47 rows × 20 columns. Header block rows 1–3 (PEDIDO, Data, Razão Social, End., Cidade, Estado,
  Prazo de Pagamento, Transp.).
- Product grid: **5 blocks of 4 columns** → quantity (A, E, I, M, Q) · unit `dz` (B, F, J, N, R) ·
  product name (C, G, K, O, S) · value column (D, H, L, P, T). Rows 4–46 (1-indexed), ~167 names.
- **189 formula records**: the value column of every product row, plus the footer totals. Values show
  0.0 now; prices are therefore **embedded in the formulas** and are not visible to the app.
- Footer labels sit in columns E and M of rows 34–46 (SUB-TOTAL / DESCONTO / TOTAL / TOTAL DE DÚZIAS
  for INCENSOS, DEFUMADORES and DEF/INC., plus TOTAL DE CAIXAS). They overlap quantity columns of
  blocks that have ended, so a "product row" is defined by a **non-empty name cell**, not by the
  quantity cell.
- Names are abbreviated and sometimes truncated ("Nossa Sra.Des.dos Nos", "S. Def.S.Paz e Proteção",
  "Abre C. da Felicidade"), with periods used without following spaces.

## D1 — How to fill the form without losing formulas

- **Decision**: the user performs a **one-time "Salvar como → .xlsx"** of the original in Excel and
  places it at `assets/PLANILHA_2024.xlsx`. The app fills **that copy** with `openpyxl`, writing
  **only the five quantity columns** and leaving everything else (including all formulas) untouched.
  The original `.xls` stays read-only in `assets/original/`.
- **Rationale**: LibreOffice (the design's assumed converter) is **not installed** on this machine.
  `xlrd` cannot read formula text, and `xlutils`/`xlwt` copying would **drop the 189 formulas**,
  silently breaking the form. A real Excel conversion keeps formulas and styles, and `openpyxl`
  preserves them on load/save.
- **Alternatives considered**: (a) install LibreOffice via Homebrew and convert in code — heavy
  download, extra dependency, unattended conversion risk; kept as fallback only if Excel is
  unavailable. (b) Rebuild the form from `xlrd` values with `openpyxl` — loses formulas. (c) Write
  `.xls` with `xlutils` — loses formulas. (d) Export from Numbers — formula fidelity uncertain.
- **Consequences**: `openpyxl` writes no cached values, so the value/total cells appear computed
  once the file is opened in Excel (set `fullCalcOnLoad`). A **template check test** asserts the
  formula count is unchanged (189) after a fill and that each quantity lands in its product's row.

## D2 — Catalog and categories

- **Decision**: build the catalog by scanning name columns C, G, K, O, S for non-empty strings in
  rows 4–46 of the `.xlsx`; the quantity cell is two columns to the left (A, E, I, M, Q).
  Category by block: blocks 1–3 (columns A–L) → **Defumadores**; blocks 4–5 (M–T) → **Incensos**;
  **Def/Inc** is the sum of both (matches the footer labels' positions).
- **Rationale**: the product names *are* the catalog (no separate list), and footer label positions
  indicate which blocks each total covers.
- **Alternatives**: a hand-typed product CSV — duplicates data and can drift from the form.
- **Confirmed** (A1, verified on the user's `.xlsx` below).

## D3 — Pipeline as LCEL Runnables

- **Decision**: `proposal = RunnableLambda(extract) | RunnableLambda(match_all) | RunnableLambda(validate)`
  where `match_all` calls `RunnableLambda(match_one).map()` over the lines. `save_corrections` and `fill_template` are two Runnables invoked at two endpoints: `save_corrections`
  on approval, `fill_template` on download (not one `|` pipe).
  Only `extract` and the optional `tie_break` inside `match_one` call the LLM; they take the chat
  model as an injectable dependency so tests pass a stub.
- **Rationale**: matches Constitution V; each stage is a plain function, unit-testable offline, and
  traceable via stored per-stage outputs.
- **Alternatives**: one big prompt (opaque); LangGraph (no loops/branching yet — YAGNI).

## D4 — Strict matching

- **Decision**: normalize (lowercase, strip accents, replace `.` with space, collapse spaces, expand
  abbreviations from `assets/abbreviations.json`) both the query and every catalog name. Order:
  1. exact normalized equality with a catalog name or alias → auto-accept;
  2. otherwise score all products with `rapidfuzz` `token_sort_ratio`; auto-accept only if
     top ≥ **95**, lead over runner-up ≥ **10**, the constitution's window guard passes (no other
     product within **15** points of the top shares its first word), **and the top product's first
     word is unique in the catalog** (spec FR-006: a fuzzy match inside a look-alike family such as
     "Abre …" or "Quebra …" is never auto-accepted). The family rule is stricter than the window
     guard and was added after checking real scores: "abre camino" scores ≈ 96 against "Abre Caminho"
     while its nearest sibling scores ≈ 59, so the window guard alone would auto-accept it;
  3. otherwise flag "revisar" with the top 3;
  4. if candidates are ambiguous, an LLM **tie-break** may *pre-select* one of the 3 (it can only
     choose from the given ids, or none); it never auto-accepts.
- **Rationale**: Constitution IV; the "Abre …" family makes similarity alone unsafe. Both sides go
  through the same normalizer so "Abre C. da Felicidade" and "abre caminho da felicidade" are exact.
- **Alternatives**: embeddings for matching — deferred (needs vector store, Constitution VII);
  `partial_ratio` — rewards substring matches ("Abre Caminho" ⊂ "Abre Caminho da Felicidade"),
  which is exactly the failure we must avoid.
- **Thresholds** live in `config.py` and are tuned against the regression set, not edited per case.

## D5 — LLM usage

- **Decision**: `langchain-anthropic` `ChatAnthropic(...).with_structured_output(<Pydantic schema>)`
  for extraction and tie-break. Model name from configuration (default a current Claude Sonnet),
  API key from `ANTHROPIC_API_KEY` in the environment. Prompts are written in pt-BR. Extraction
  schema: `[{texto, quantidade, unidade}]`; tie-break schema: `{produto_id | null}`.
- **Rationale**: structured output avoids parsing free text; one retry on malformed output then the
  manual-table fallback (spec FR-017).
- **Alternatives**: raw `anthropic` SDK — fine, but LangChain gives the Runnable interface already
  chosen for the learning goal.

## D6 — Storage

- **Decision**: stdlib `sqlite3`, schema created at startup; tables `catalog`, `aliases`, `runs`,
  `run_lines` (see [data-model.md](data-model.md)). Catalog and seed aliases rebuilt from the template
  when the `.xlsx` changes.
- **Rationale**: one user, simple relations; an ORM would add weight for no benefit (Constitution VII).

## D7 — Web interface

- **Decision**: FastAPI serving one Jinja2 page plus a small vanilla-JS editable table; JSON
  endpoints in [contracts/http-api.md](contracts/http-api.md). All strings pt-BR. No JS build step.
- **Rationale**: simplest thing a non-technical user can run locally; `TestClient` makes contract tests easy.
- **Alternatives**: Streamlit/Gradio (less control over editable review table and blocking approval).

## D8 — Testing approach (Constitution II)

- **Decision**: test-first at three layers — unit (normalize, match, validate, catalog, export, store),
  contract (HTTP + pt-BR errors), integration (paste → approve → export with stubbed LLM). The
  ~20-message regression set in `tests/fixtures/mensagens/` and the "must never confuse" cases
  (Abre Caminho vs Abre C. da Felicidade vs Abre C. do Dinheiro, typo inside the family) are authored
  **before** `match`/`extract` code. A separate **manual** script runs the real API on the set.
- **Rationale**: pins the subtle matching rules down before implementation convenience erodes them.

## D9 — Python and packaging

- **Decision**: Python 3.11 with `uv` (`pyproject.toml`, locked). Installed here already.
- **Rationale**: 3.11 is installed and broadly supported by the dependencies above; the system
  Python 3.9 is too old.

## Verified on the user's `.xlsx` (2026-10-23)

The user supplied `PLANILHA-2024.xlsx` (saved from Excel; sheets Plan1–Plan3, Plan1 used). Inspected with `openpyxl`:

- **189 formulas preserved**; **178 non-empty cells** in the name columns C, G, K, O, S (rows 4–46), of which **11 are footer formulas** (e.g. `=SUM(M4:M32,Q4:Q31)` in columns K and S) and **167 are products**; the catalog loader must skip any cell whose text starts with `=`.
- Value formulas embed the price per row, e.g. `D4 = A4*27`, `H4 = E4*23`, `T30 = Q30*15.4` (some written with a leading space, `= I4*23`). The app never reads or writes them.
- **A1 confirmed** by the footer formulas: Defumadores = blocks 1–3 (`K46 = SUM(A4:A46,E4:E42,I4:I41)`);
  Incensos = blocks 4–5 (`S37 = SUM(M4:M32,Q4:Q31)`); Def/Inc = `K46 + S37` (`S44`).
- The sheet itself computes total dozens and boxes: `T46 = S44/10`, `Q46 = ROUNDUP(T46,0)`. The app's
  on-screen totals can therefore be cross-checked against these cells in a test.
- Discount cells (`T35` for Incensos, `L44` for Defumadores) are user inputs; the app does not touch them.
- **Header input cells** (merged, next to each label, must stay empty): `Q1` (Data), `D2` (Razão
  Social), `I2` (End.), `D3` (Cidade), `I3` (Estado), `M3` (Prazo de Pagamento), `Q3` (Transp.);
  the labels (`P1`, `A2`, `H2`, `A3`, `H3`, `K3`, `P3`) must stay unchanged.
- Header/footer cells are **merged** (e.g. `A2:C2`, `E43:J46`, `M36:R36`). A test must assert no
  quantity cell the exporter writes to is a merged cell.

## Assumptions

- **A1 — Categories by block:** CONFIRMED (above).
- **A2 — One-time Excel step:** DONE; the user provided the `.xlsx`. It is copied to
  `assets/PLANILHA_2024.xlsx` as the first setup task; the original `.xls` goes to `assets/original/`.

## Threshold tuning evidence (T061, 2026-10-23)

Swept `min_score` ∈ {80, 85, 90, 95, 98} × `min_lead` ∈ {5, 10, 20} with the first-word family guard
on, over the 49 regression lines and 294 synthetic probes (every catalog product with one character
dropped or doubled, fixed seed):

| score | lead | regression wrong auto-accepts | probe wrong auto-accepts | probes auto-accepted |
|---|---|---|---|---|
| 80–90 | 5–10 | 0 | 0 | 121–123 of 294 (≈ 41%) |
| **95** | **10** | **0** | **0** | **75 of 294 (≈ 25%)** |
| 98 | any | 0 | 0 | 2 of 294 |

- **No threshold combination produced a wrong auto-accept.** The safety comes from the family guard
  (a fuzzy match in a first-word family is never accepted) and from exact/alias-only acceptance;
  score and lead only decide how many unambiguous typos need no click.
- **Decision: keep 95 / 10 / 15** (the constitution's values). Lowering the score to 90 would
  auto-accept more typos on these probes, but one-character typos are not what real customers
  produce, so the conservative setting stays until real messages say otherwise. Re-run
  `scripts/run_regression_real.py` and this sweep when real messages are added to the regression set.
- Offline run with canned extractions: SC-001 = 45/46 lines right without an edit (98%; the miss is
  "sete linhas" → candidate "Sete Flechas", which only the LLM tie-break can resolve), SC-002 = 0
  wrong auto-accepts and 0 unflagged lines. SC-001 with the real LLM is measured in T062.

## Addendum (2026-10-24) — ambiguous abbreviations match as full wordings

The "S." in "S. Def.S.Paz e Proteção" can mean **santo, santa or saúde** (told by the user, who can't say
which). Expanding it to one word would be wrong for the others, and leaving it to fuzzy matching would
reward partial overlap, so the match is made on the **complete wording**:

- `assets/abbreviations.json` has a new `variantes` section: `"s": ["santo", "santa", "saude"]`.
- `normalize_variants` turns a catalog name into every full wording: each "S." becomes one of its meanings
  **or stays as written**, in every combination. The product above has 4 × 4 = **16 exact forms**; every
  other product has exactly one. A form that would belong to two products makes the catalog load fail.
- The matcher accepts a line automatically only when the **whole** wording equals one of those forms
  (accents and case ignored). "santa defesa paz e protecao" (a word missing) or "santo defesa" (a piece)
  are **not** matches: they are flagged with candidates.
- Fuzzy scoring uses the best form, but the **family guard looks at the first word of every form**: since
  "santa …" and "santo …" start other products too (Santa Rita, Santo Antonio, …), a near-miss such as
  "santa defesa santa paz e protecaoo" is never auto-accepted, even at ~99% similarity.
- Regression message `22_santa_defesa.txt` covers it. Evidence: 373 tests; the offline regression is 48/49
  lines right without an edit (98%) with 0 wrong auto-accepts.
