# Data Model: Produção e acesso

## `schema_migrations` (new, created by the runner)

| Column | Type | Notes |
|---|---|---|
| `versao` | text PK | `0001`, `0002`... (the numeric prefix of the file) |
| `arquivo` | text | file name |
| `checksum` | text | SHA-256 of the raw file |
| `aplicada_em` | timestamptz | default now() |

## `uso_diario` (new, migration 0002)

| Column | Type | Notes |
|---|---|---|
| `conversa` | text | the conversation id (phone number or consumer id) |
| `dia` | date | the day in America/Sao_Paulo |
| `mensagens` | integer not null default 0 | accepted messages that day |

Primary key `(conversa, dia)`. Row-level security enabled, no policies. Rows are never deleted by the
application (a cleanup of old days can be a later migration or a scheduled job).

## Unchanged tables

`catalog`, `pedidos`, `apelidos`, `modelos` exactly as after feature 005 (they form the baseline `0001`).

## Not stored

API keys, message text in logs, phone numbers in logs.
