# Data Model: Banco único, serviços de IA configuráveis e memória de pedidos

Database: Postgres 16 + pgvector, schema **`pedido`**. Created by one idempotent `schema.sql`
(rendered with `{dim}` = `EMBED_DIMENSIONS`, default 1024). The four tables of 001 keep their meaning;
this feature adds one column to `runs` and two memory tables. Row-level security is enabled on every
table with **no policies** (a hosted REST API then exposes nothing; the application connects as the
table owner).

## Tables kept from 001 (now Postgres types)

| Table | Changes |
|---|---|
| `catalog` | `id integer PK`, `nome`, `nome_normalizado`, `categoria`, `bloco integer`, `linha integer`, `celula_qtd` — unchanged |
| `aliases` | `texto_normalizado text PK`, `produto_id → catalog`, `origem text default 'correcao'`, `criado_em timestamptz` — unchanged |
| `runs` | `id bigint identity PK`, `mensagem`, `criado_em timestamptz default now()`, `aprovado_em timestamptz null`, `estado text` (`proposto` → `aprovado`), **new** `memoria_estado text` |
| `run_lines` | same columns; `precisa_revisao`/`confirmado` are `boolean`, `candidatos`/`flags` are `jsonb`, `confianca`/`qtd_*` are `double precision` |

`runs.memoria_estado` ∈ `nao_aplicavel` (default; a proposal not yet approved, or an order approved while
the embeddings were not configured — the reprocess command backfills those) | `pendente` (approved,
some vector missing) | `completa` (approved, every vector present). Transitions: `nao_aplicavel` →
(approval) → `completa` or `pendente`; `pendente` → (reprocess) → `completa`. It never changes an
approval's `estado`.

## memoria_linhas — remembered line (RAG, line level)

| Field | Type | Notes |
|---|---|---|
| `id` | bigint identity PK | |
| `texto` | text, not null | the written text of a final approved line, as the customer wrote it |
| `texto_normalizado` | text, not null | output of the normalizer (the same one used by aliases) |
| `produto_id` | integer → catalog, not null | the product the user confirmed |
| `run_id` | bigint → runs | the approval that produced it |
| `embedding` | `vector({dim})`, **null allowed** | null = pending (embedder was unavailable) |
| `modelo_embedding` | text, not null | the embedding model configured when written; updated by reprocess |
| `confirmado_em` | timestamptz, not null | refreshed on every re-confirmation (recency tie-break) |

Unique key: `(texto_normalizado, produto_id, modelo_embedding)`. Index: HNSW on `embedding`
(`vector_cosine_ops`). Never stored: removed lines, unconfirmed suggestions, lines with empty `texto`.

## memoria_mensagens — remembered message (RAG, message level)

| Field | Type | Notes |
|---|---|---|
| `id` | bigint identity PK | |
| `run_id` | bigint → runs, **unique** | one memory per approved run |
| `mensagem` | text, not null | the complete message (never truncated in storage) |
| `linhas` | jsonb, not null | final approved lines: `[{texto, quantidade, unidade, produto}]` |
| `embedding` | `vector({dim})`, null allowed | the message text, truncated to 2,000 characters before embedding |
| `modelo_embedding` | text, not null | as above |
| `confirmado_em` | timestamptz, not null | |

Index: HNSW on `embedding`.

## Validation rules

- A memory row is created only at approval, from the run's **final** lines (`produto_final` not null,
  `qtd_final` valid, `texto` not empty after trimming).
- Help queries only use rows with `embedding IS NOT NULL` and `modelo_embedding = EMBED_MODEL`.
- Reprocess selects rows with `embedding IS NULL` **or** `modelo_embedding <> EMBED_MODEL`; if updating
  would collide with the unique key, the older duplicate row is dropped.
- The database dimension must equal `EMBED_DIMENSIONS`; otherwise startup refuses (research D2).
- Keys and secrets are never part of any table.

## Derived values (not stored)

- History `memoria` field: `memoria_estado = 'completa'` → "memorizado"; `'pendente'` → "pendente";
  otherwise absent.
- Line-level neighbor query (cosine): `1 - (embedding <=> :query)` as similarity, ordered by
  `embedding <=> :query`, then `confirmado_em DESC`.

## Relationships

`runs 1—N run_lines`; `runs 1—1 memoria_mensagens`; `runs 1—N memoria_linhas`;
`memoria_linhas N—1 catalog`; `aliases N—1 catalog`. The alias table and the memory are independent:
an alias makes an exact match (auto-accept, as in 001); memory only advises.
