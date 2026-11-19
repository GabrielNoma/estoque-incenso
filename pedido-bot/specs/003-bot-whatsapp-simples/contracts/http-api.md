# Contract: HTTP API of the test chat

Customer-facing text is pt-BR. The engine never raises to the caller: every failure is a normal reply.

## POST `/api/mensagem`

Request: `{ "telefone": "5511999990000", "texto": "2 dz abre caminho, meia dúzia de arruda" }`

`200` → `{ "resposta": "<reply text>", "arquivo": null | { "nome": "pedido-12.xlsx", "url": "/api/pedidos/12/planilha" } }`

- An order → `resposta` is the list followed by a blank line and `ok ou não?`; `arquivo` is null.
- ok with a pending order → `resposta` is the confirmation sentence and `arquivo` is set.
- Every other case → one short neutral sentence (see `replies.md`) and `arquivo` null.
- Missing or non-string `telefone`/`texto` → `422` `{"erro": "requisicao_invalida", "mensagem": "<pt-BR>"}`.
- An empty `texto` is a normal message (reply `SEM_ITENS`).

## GET `/api/pedidos/{id}/planilha`

`200` → the `.xlsx` (attachment `pedido-{id}.xlsx`), regenerated from the stored items, only for a
`confirmado` order. `404` `pedido_nao_encontrado` for an unknown id; `409` `pedido_nao_confirmado` for an
order that is not confirmed. Error bodies are `{"erro": code, "mensagem": "<pt-BR>"}`.

## GET `/`

The chat page.

## Guarantees tested at contract level

1. The reply to an order is exactly the list plus `ok ou não?` and nothing else.
2. No `arquivo` before ok; none for a second ok.
3. Conversations of different phone numbers do not interfere.
4. Every error body and reply is pt-BR.
