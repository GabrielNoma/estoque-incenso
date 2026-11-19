# Research: Modelo de planilha gerenciado

No `NEEDS CLARIFICATION` remains.

## D1 — Where the model lives

Table `pedido.modelos(id, versao, arquivo, conteudo bytea, produtos, ativo, criado_em)`. `versao` is a
unique increasing integer; a unique partial index allows ONE row with `ativo`. Nothing is deleted. At
startup, if the table is empty, `assets/PLANILHA_2024.xlsx` is installed as version 1 (seed). Importing runs
in one transaction under an advisory lock: deactivate the old, insert the new (`versao = max + 1`, active).

## D2 — Validation of an uploaded model (`catalog.validar_modelo`)

In this order, the first failure wins, each a constant pt-BR sentence that ends by asking to check the
model: size above `MAX_MODELO_MB` (413); empty body or old binary `.xls` (starts with `D0 CF 11 E0`) → "salve
como .xlsx"; not a zip / not readable by openpyxl; no product in the expected cells; two products with the
same normalized name (the name is quoted); a merged quantity cell (the cell is named). The layout is the one
of `catalog.py` (names C, G, K, O, S; rows 4 to 46; quantity two columns to the left). The catalog is built
by the same `load_catalog`, now accepting bytes, so what is validated is exactly what will be used.

## D3 — Comparison

By position (`id = block * 1000 + row`) and name: **added** = ids only in the new; **removed** = ids only in
the old; **renamed** = same id, different name (`de`, `para`). A product moved to another row is therefore
removed plus added; the answer tells it, and its nicknames are disabled (safe side).

## D4 — Active catalog on every message

`ModeloService.atual()` returns `ModeloAtivo(versao, arquivo, catalog, conteudo)`. It asks the database for
the active version (one cheap query) and rebuilds the catalog only when it changed. A model that cannot be
read or has no products raises `ModeloIndisponivel`. `Conversa` caches the `Matcher` and the chains per
version. A plain list of products is still accepted by `Conversa` (a static model), so earlier tests keep
working.

## D5 — Model problems in the conversation

- An order while the model is unavailable → `MODELO_INVALIDO`, nothing stored, pending kept.
- `ok` while a product of the pending order is missing, or its name at that position differs (compared with
  the `nome` stored in the order's items), or the cell is gone → `MODELO_PRODUTO_AUSENTE`, no file, pending
  kept. `quantities_for_export` now refuses an unknown product instead of silently dropping it.
- The matching is not touched: closest product of the active model, never a doubt reported.

## D6 — Orders remember their model

`pedidos.modelo_versao` is set when the order is confirmed. `GET /api/pedidos/{id}/planilha` regenerates the
Excel from THAT version (`ModeloService.por_versao`), so a confirmed order stays reproducible after the model
changes.

## D7 — Nicknames follow the model

`apelidos.produto_nome` is filled when a nickname is learned and, for older rows, at startup. On every
activation `store.sincronizar_apelidos(catalog)` disables (status `desativado`) each nickname whose
`produto_id` is missing or whose name differs from the product at that id, and fills missing names. Rows are
never deleted; the script of 004 can re-enable one.

## D8 — HTTP

`POST /api/modelo` reads the raw body (`request.body()`), takes the name from `X-Nome-Arquivo` (default
`modelo.xlsx`), and answers 200 with the summary, 413 when too large, 422 `modelo_invalido` with the specific
message. `GET /api/modelo` returns the active file (`modelo-pedido.xlsx`). `GET /api/modelo/info` returns the
version data. All errors are `{"erro", "mensagem"}`.

## D9 — What does not change

Replies for normal orders, the memory (004), the guardrails, the chat page of 003 and the states of orders.

## Medição final (2026-11-18)

- 514 testes verdes (Postgres com pgvector real; modelos de teste montados com openpyxl a partir do modelo original).
- Com o app real e o Ollama: exportar o modelo (18 KB, 167 produtos); importar uma cópia com "Incenso Teste Real" em uma linha livre (versão 2, `adicionados` correto, sem reiniciar); o pedido "2 dz de incenso teste real e meia duzia de arruda" saiu como `Arruda — 0,5 dz` e `Incenso Teste Real — 2 dz`, e o `ok` devolveu a planilha; um arquivo inválido devolveu uma única mensagem em português e `GET /api/modelo/info` manteve a versão 2.
- O modelo original foi reimportado ao final (volta ao conteúdo original como versão 3; as versões 1 e 2 continuam guardadas).
- Observação: o produto movido de linha conta como removido mais adicionado (D3).
