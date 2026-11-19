# Data Model: Memória silenciosa de apelidos e guardrails

Schema `pedido` (Postgres, extension `vector`). Row-level security enabled with no policies, as before.

## `apelidos` (new)

| Column | Type | Notes |
|---|---|---|
| `id` | bigint identity PK | shown by the script |
| `texto_normalizado` | text not null | normalized written wording |
| `produto_id` | integer not null | product of the catalog |
| `embedding` | vector(N), nullable | N = `EMBED_DIMENSIONS`, fixed at creation |
| `modelo` | text, nullable | name of the embedding model (null when `embedding` is null) |
| `positivos` | integer not null default 0 | confirmations |
| `negativos` | integer not null default 0 | refusals / replacements |
| `status` | text check in (`ativo`, `desativado`) default `ativo` | switched by the script |
| `criado_em`, `atualizado_em` | timestamptz | |

Unique `(texto_normalizado, produto_id)`. Index on `texto_normalizado`; an HNSW (cosine) index on
`embedding`. **Applies** when `status = 'ativo' and positivos >= 2 and positivos > negativos`.

## `pedidos` (changed)

New column `linhas jsonb not null default '[]'`: the matched lines before summing,
`[{"texto": "abre c felicidade", "quantidade": 1.0, "produto_id": 1005}]`. `itens` is unchanged.

## States and transitions

Order states are those of 003 (forward only). Memory writes happen at these transitions:

| Transition | Memory effect |
|---|---|
| aguardando → confirmado | upsert each non-exact line pair: `positivos + 1` (with embedding) |
| aguardando → recusado | existing pairs of its lines: `negativos + 1` |
| aguardando → substituido | existing pairs of its lines: `negativos + 1` |

## Not stored

Phone numbers in logs, message text in logs, API keys, rate-limit counters (memory only).
