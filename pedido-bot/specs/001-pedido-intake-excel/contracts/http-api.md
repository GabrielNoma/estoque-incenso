# HTTP Contract: Pedido a partir de mensagem de WhatsApp

Local web tool; one HTML page plus JSON endpoints. All user-visible text and **all error messages
are in pt-BR** (Constitution I). Errors use a single shape:

```json
{ "erro": "codigo_curto", "mensagem": "Texto claro em português para o usuário." }
```

## Page

| Method | Path | Description |
|---|---|---|
| GET | `/` | The pt-BR page: paste box, review table, approve/download, history list |

## API

### POST `/api/pedidos` — create a proposal (runs Chain 1)

Request: `{ "mensagem": "texto colado" }`

- `200` → `{ "id": 12, "estado": "proposto", "linhas": [Linha], "totais": Totais }`;
  when nothing is recognized, `linhas` is empty and `"aviso": "Não encontrei nenhum pedido nessa
  mensagem. Preencha a tabela manualmente."` is included
- `400` `mensagem_vazia` → "Cole a mensagem do cliente antes de analisar."
- `502` `analise_indisponivel` → "Não foi possível analisar a mensagem agora. Sua mensagem foi
  mantida; tente novamente ou preencha a tabela manualmente." (response also includes `id` and an
  empty `linhas`, so the run exists and the table can be filled by hand — FR-017)

`Linha`:

```json
{
  "id": 301,
  "texto": "abre c felicidade",
  "quantidade": 2.0,
  "unidade": "dz",
  "produto": { "id": 7, "nome": "Abre C. da Felicidade", "categoria": "Defumadores" },
  "confianca": 0.82,
  "motivo": "candidatos",
  "candidatos": [ { "produto_id": 7, "nome": "Abre C. da Felicidade", "pontuacao": 82 },
                  { "produto_id": 4, "nome": "Abre Caminho", "pontuacao": 74 } ],
  "flags": [ "revisar" ],
  "precisa_revisao": true,
  "origem_linha": "extraida"
}
```

`produto` may be `null` (unmatched). `Totais`: `{ "Defumadores": 12.5, "Incensos": 4.0, "Def/Inc": 16.5 }`.

### GET `/api/catalogo?q=texto` — search products for the dropdown

- `200` → `[ { "id": 7, "nome": "Abre C. da Felicidade", "categoria": "Defumadores" } ]`
  (accent/case-insensitive substring over normalized names, max 20)

### POST `/api/pedidos/{id}/aprovar` — approve (runs Chain 2 save step)

Request: the user's final table:

```json
{ "linhas": [ { "id": 301, "produto_id": 7, "quantidade": 2.0, "confirmado": true },
              { "id": null, "produto_id": 15, "quantidade": 0.5, "confirmado": true } ] }
```

(`id: null` = line added by the user; a line omitted from the list is treated as removed. The client
sends `confirmado: true` only for lines the user explicitly confirmed or edited; it is required only for
`precisa_revisao` lines. Merging duplicates is done by the client: it sends one line with the quantities
added, and omits the other.)

- `200` → `{ "id": 12, "estado": "aprovado", "totais": Totais, "download": "/api/pedidos/12/planilha" }`
- `409` `linhas_pendentes` → "Há linhas sem produto, com quantidade inválida, repetidas ou não confirmadas. Corrija as linhas
  destacadas antes de aprovar." — body includes `"linhas_pendentes": [301, ...]` (FR-010)
- `404` `pedido_nao_encontrado` → "Pedido não encontrado."
- Side effects on success: run becomes `aprovado`; aliases created/updated (FR-014); final answers
  stored next to suggestions (FR-015).

### GET `/api/pedidos/{id}/planilha` — download the filled form

- `200` → `.xlsx` file (`Content-Disposition: attachment; filename="pedido-12.xlsx"`)
- `409` `pedido_nao_aprovado` → "Aprove o pedido antes de gerar a planilha." (FR-011)
- `500` `falha_planilha` → "Não foi possível gerar a planilha. O pedido aprovado continua salvo;
  tente novamente." (FR-018)
- Guarantees: only the five quantity columns of the copy are written; header left blank (FR-013);
  all 189 template formulas intact; original `.xls` never modified (FR-012).

### GET `/api/pedidos` and GET `/api/pedidos/{id}` — history

- list → `[ { "id", "criado_em", "aprovado_em", "estado", "resumo": "3 linhas, 1 a revisar" } ]`
- detail → same shape as the proposal response, with for each line the **suggestion and the final
  answer side by side** (`produto_sugerido`, `confianca`, `produto_final`, `qtd_final`) (FR-015).

## Additional error codes

| Code | Status | Message (pt-BR) |
|---|---|---|
| `pedido_ja_aprovado` | 409 | "Este pedido já foi aprovado." |
| `requisicao_invalida` | 422 | "A requisição não é válida. Confira os dados enviados e tente novamente." |
| `erro_interno` | 500 | "Algo deu errado do nosso lado. Tente novamente em instantes." |

An extraction that fails is retried once before `analise_indisponivel` (502) is returned.

## Behavior guarantees tested at contract level

1. Approving with any unresolved line (no product, invalid quantity, duplicate product, or a
   `precisa_revisao` line without `confirmado: true`) returns `409` and changes nothing.
2. Downloading before approval returns `409`.
3. Every error body has pt-BR `mensagem`.
4. A repeated phrase confirmed once is returned with `motivo: "alias"` and no `revisar` flag in the
   next proposal.
