# Contract: changes to the HTTP API of 001

Everything in `specs/001-pedido-intake-excel/contracts/http-api.md` stays as is (paths, status
codes, error bodies, approval rules). Only the following is added. All text is pt-BR.

## Proposal and detail lines (`Linha`)

- `motivo` gains the value **`memoria`** (a remembered line pre-selected the product).
- New `motivo_rotulo`: `"parecido com um pedido anterior"` when `motivo == "memoria"`, otherwise `null`.
- Each entry of `candidatos` gains `origem`: `"texto"` (text similarity) or `"memoria"`.
- A line with `motivo: "memoria"` always has `precisa_revisao: true` and the flag `revisar`: it is
  **never** auto-accepted and approval still requires `confirmado`.

## History

- List items and detail gain `memoria`: `"memorizado"` | `"pendente"` | `null`, and
  `memoria_rotulo`: `"Memorizado"` | `"Memória pendente"` | `null` (null while the order is only proposed).
- `POST /api/pedidos/{id}/aprovar` response gains the same `memoria` / `memoria_rotulo`, so the page can
  say the memory is pending when the embeddings service was unavailable. The approval itself is
  unaffected (still `200`, `estado: "aprovado"`).

## New error

| Code | Status | Message |
|---|---|---|
| `erro_banco` | 503 | "Não foi possível acessar o banco de dados agora. Tente novamente em instantes; nada foi salvo pela metade." |

Returned whenever a database operation fails while the tool is running; every approval is a single
transaction, so no order is left partly saved, and the tool works again once the database returns.

## Behavior guarantees tested at contract level

1. An approval succeeds (`200`) even when the embeddings service fails or times out, and the order
   shows `memoria: "pendente"` in the history.
2. After the approval of a corrected line, a later proposal for a similar wording returns `motivo:
   "memoria"` with `precisa_revisao: true`, and `aprovar` still returns `409` until `confirmado` is sent.
3. A remembered "abre caminho" never yields `motivo: "memoria"` for "abre caminho da felicidade".
4. With the embedder unconfigured or failing, proposals are identical to 001.
5. No response, history entry or stored row contains a key.
