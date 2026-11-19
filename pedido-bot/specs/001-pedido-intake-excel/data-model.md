# Data Model: Pedido a partir de mensagem de WhatsApp

> **Atualização (feature 002):** o armazenamento deste projeto mudou de SQLite para **Postgres com pgvector** (schema `pedido`, `DATABASE_URL` obrigatória). Onde este documento falar de SQLite ou `data/pedido.db`, vale o que está em `specs/002-rag-memory-providers/`. O restante continua válido.


Storage: SQLite (`data/pedido.db`). Entities map to the spec's Key Entities.

## catalog — Product

Rebuilt from the `.xlsx` template whenever it changes.

| Field | Type | Notes |
|---|---|---|
| `id` | integer, PK | stable per (bloco, linha) |
| `nome` | text, not null | exactly as written on the form |
| `nome_normalizado` | text, not null | output of the normalizer (abbreviations expanded) |
| `categoria` | text, not null | `Defumadores` or `Incensos` (see research A1); `Def/Inc` is derived |
| `bloco` | integer 1–5 | column block on the form |
| `linha` | integer | 1-indexed sheet row |
| `celula_qtd` | text | quantity cell, e.g. `A4` (name column − 2) |

Validation: `nome_normalizado` is unique within the catalog (a duplicate means a normalizer or
abbreviation bug and fails the catalog load loudly).

## aliases — Remembered phrase

| Field | Type | Notes |
|---|---|---|
| `texto_normalizado` | text, PK | normalized written phrase |
| `produto_id` | integer, FK → catalog | exactly one product per phrase |
| `origem` | text | always `correcao` (the user confirmed or corrected the match); catalog names are matched exactly and are not seeded as aliases |
| `criado_em` | datetime | |

Rules: an alias is created only for a line the user **confirmed or changed** (never for lines accepted
automatically and left untouched); a phrase maps to one product; if the user later maps the same phrase elsewhere, the alias is
**updated** (latest confirmation wins) and the change is visible in the run history.

## runs — Message run

| Field | Type | Notes |
|---|---|---|
| `id` | integer, PK | |
| `mensagem` | text, not null | exactly as pasted |
| `criado_em` | datetime | |
| `aprovado_em` | datetime, null | set on approval |
| `estado` | text | `proposto` → `aprovado` |

State transitions: `proposto` → `aprovado` only via an approval request with no unresolved lines.
An approved run is immutable; exporting it again is always allowed.

## run_lines — Run line

Suggestion and final answer are stored **side by side** (Constitution VI).

| Field | Type | Notes |
|---|---|---|
| `id` | integer, PK | |
| `run_id` | integer, FK → runs | |
| `ordem` | integer | position in the table |
| `texto` | text | written product name from the message ("" for a line the user added) |
| `qtd_extraida` | real, null | quantity the system extracted, in dozens |
| `unidade_extraida` | text, null | unit as written (flagged if not dozens) |
| `produto_sugerido` | integer, null, FK | system's suggestion |
| `confianca` | real, null | 0–1 certainty: `exato`/`alias` = 1.0; fuzzy = score ÷ 100 (an LLM pre-selection keeps the fuzzy score of that product) |
| `precisa_revisao` | boolean | true for every line not auto-accepted (`candidatos`, `llm_sugestao`, `sem_correspondencia`) |
| `confirmado` | boolean | true once the user explicitly confirmed or changed the product (required when `precisa_revisao`) |
| `motivo` | text | `exato`, `alias`, `fuzzy_seguro`, `candidatos`, `llm_sugestao`, `sem_correspondencia` |
| `candidatos` | text (JSON) | up to 3 `{produto_id, pontuacao}` shown for review |
| `flags` | text (JSON) | list of pt-BR flag codes (below) |
| `produto_final` | integer, null, FK | what the user approved |
| `qtd_final` | real, null | quantity the user approved |
| `origem_linha` | text | `extraida`, `adicionada` |

Flag codes (displayed in pt-BR): `revisar`, `sem_produto`, `baixa_confianca` (suggestion with `confianca` below `LOW_CONFIDENCE`, initial 0.90, set in
`config.py`), `quantidade_invalida`, `unidade_nao_duzia`, `duplicado`, `texto_alterado` (the text the model returned is not literally in
the customer's message: an automatic match is downgraded to `motivo = "texto_alterado"` and needs confirmation).

## Validation rules (from the spec)

- **Quantity**: positive and a multiple of 0.5, else `quantidade_invalida` (FR-007).
- **Unit**: anything other than dozens → `unidade_nao_duzia`.
- **Duplicate**: two lines with the same final/suggested product → `duplicado`. The user resolves it with
  **Mesclar**, which keeps one line with the quantities added.
- **Unresolved** = no product chosen, invalid quantity, a `duplicado` pair, or `precisa_revisao` without
  `confirmado`; approval requires zero unresolved (FR-010). A suggested product on a `revisar` line is
  never a choice until confirmed.
- No row is ever deleted by the system; a user-removed line is kept with `qtd_final` null and
  `produto_final` null so history still shows what was suggested.

## Derived values (not stored)

- Total dozens per category (`Defumadores`, `Incensos`, `Def/Inc`) = sum of `qtd_final` (or the
  suggestion during review) grouped by `catalog.categoria`.

## Relationships

`runs 1—N run_lines`; `run_lines N—1 catalog` (suggested and final); `aliases N—1 catalog`.
Approving a run creates/updates an alias for (a) every `precisa_revisao` line with `confirmado` true and
(b) every line whose `produto_final` differs from `produto_sugerido`; never for an auto-accepted line
the user did not change (even if `confirmado` is sent true), and never for a line with an empty `texto`
(a line the user added).
