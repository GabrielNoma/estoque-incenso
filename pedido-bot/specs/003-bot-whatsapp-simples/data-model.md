# Data Model: Bot de pedidos simples

Database: Postgres, schema `pedido`, no extension required. One idempotent `schema.sql`; row-level
security enabled on every table with no policies.

## catalog — Product (kept)

`id integer PK` (block × 1000 + row), `nome`, `nome_normalizado`, `categoria`, `bloco`, `linha`,
`celula_qtd` — rebuilt from the `.xlsx` template at startup. The Excel order of a product is
`(bloco, linha)`.

## pedidos — Order (new)

| Field | Type | Notes |
|---|---|---|
| `id` | bigint identity PK | |
| `telefone` | text, not null | the customer's phone number (the conversation key) |
| `mensagem` | text, not null | the order message exactly as received |
| `itens` | jsonb, not null | the list sent: `[{produto_id, nome, quantidade}]` in Excel order |
| `lista` | text, not null | the reply text sent to the customer (list + closing line) |
| `estado` | text, not null | `aguardando` → `confirmado` \| `recusado` \| `substituido` |
| `resposta` | text, null | the customer's answer that closed the order (ok / não text) |
| `criado_em` | timestamptz, not null | |
| `respondido_em` | timestamptz, null | when the state left `aguardando` |

Index on `(telefone, id desc)`.

## Rules

- **At most one `aguardando` per phone number**: creating an order marks the previous one `substituido` in
  the same transaction.
- **Forward-only states**: `aguardando` → one of the other three; a closed order never changes again.
- A `confirmado` order's Excel is regenerated from `itens` (never stored).
- No key or secret is ever stored.

## Removed (cleanup of 001/002)

`aliases`, `runs`, `run_lines`, `memoria_linhas`, `memoria_mensagens`, and the `vector` extension: dropped
once, only if present.
