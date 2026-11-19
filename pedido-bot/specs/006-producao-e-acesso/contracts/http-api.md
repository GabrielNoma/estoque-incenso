# Contract: access rules of the HTTP API

Every error is JSON `{"erro": code, "mensagem": "<pt-BR>"}`.

| Route | Needs | Notes |
|---|---|---|
| `GET /saude` | nothing | 200 `{"status":"ok"}` or 503 `{"status":"indisponivel"}`, nothing else |
| `POST /api/mensagem` | scope `conversa` | body up to 64 KB (413 `corpo_grande` above) |
| `GET /api/pedidos/{id}/planilha` | scope `conversa` | |
| `GET /api/modelo`, `POST /api/modelo`, `GET /api/modelo/info` | scope `modelo` | upload keeps its own size limit |
| `GET /`, `/static/*`, `/docs`, `/redoc`, `/openapi.json` | (local only) | 404 when `ENVIRONMENT=producao` |

Key: `Authorization: Bearer <key>` (wins) or `X-API-Key: <key>`.

| Status | `erro` | When |
|---|---|---|
| 401 | `chave_ausente` | no key sent |
| 401 | `chave_invalida` | key unknown |
| 403 | `sem_permissao` | key without the route's scope |
| 413 | `corpo_grande` | message body above the limit |
| 429 | `muitas_requisicoes` | the key's per-minute limit exceeded |

Replies to customers (`resposta` of `POST /api/mensagem`) for the daily limit and the busy case are normal
texts (see `messages.md`).
