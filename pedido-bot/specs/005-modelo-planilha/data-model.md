# Data Model: Modelo de planilha gerenciado

## `modelos` (new)

| Column | Type | Notes |
|---|---|---|
| `id` | bigint identity PK | |
| `versao` | integer not null unique | 1 is the seed |
| `arquivo` | text not null | original file name (default `modelo.xlsx`) |
| `conteudo` | bytea not null | the `.xlsx` bytes, never changed |
| `produtos` | integer not null | products read from it |
| `ativo` | boolean not null default false | unique partial index: at most one `true` |
| `criado_em` | timestamptz default now() | activation time |

Row-level security enabled, no policies. No delete is ever issued by the application.

## Changed tables

- `pedidos.modelo_versao integer null`: the model version the Excel of a confirmed order was filled with.
- `apelidos.produto_nome text null`: the name of the product the nickname was confirmed for.

## Transitions

| Event | Effect |
|---|---|
| start with no model | seed installed as version 1, active |
| valid import | old model `ativo = false`, new row active, catalog rebuilt, nicknames synchronized |
| invalid import | nothing changes |
| order confirmed | `pedidos.modelo_versao` = active version |
