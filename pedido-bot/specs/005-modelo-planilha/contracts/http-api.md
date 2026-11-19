# Contract: HTTP API of the model

Errors are JSON `{"erro": code, "mensagem": "<pt-BR>"}`. No sign-in (local use).

## GET `/api/modelo`
`200` the active model, `Content-Disposition: attachment; filename="modelo-pedido.xlsx"`, type
`application/vnd.openxmlformats-officedocument.spreadsheetml.sheet`.

## POST `/api/modelo`
Body: the raw `.xlsx` bytes (content type xlsx or `application/octet-stream`). Optional header
`X-Nome-Arquivo` (the original file name, URL-decoded, default `modelo.xlsx`).

`200`:
```json
{"versao": 2, "arquivo": "novo.xlsx", "produtos": 168,
 "adicionados": ["Incenso Novo"], "removidos": [], "renomeados": [{"de": "Alecrim", "para": "Alecrim Puro"}],
 "apelidos_desativados": 0}
```
`413 modelo_grande` too large. `422 modelo_invalido` with the specific message (see `replies.md`). The active
model never changes on an error.

## GET `/api/modelo/info`
`200 {"versao": 2, "arquivo": "novo.xlsx", "produtos": 168, "ativado_em": "2026-11-18T10:00:00"}`.

## GET `/api/pedidos/{id}/planilha` (changed)
Regenerated from the model version the order was confirmed with.

## POST `/api/mensagem` (unchanged shape)
New neutral replies are normal `resposta` texts (see `replies.md`).
