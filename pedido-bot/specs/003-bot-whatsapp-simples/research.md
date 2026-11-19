# Research: Bot de pedidos simples (estilo WhatsApp)

No `NEEDS CLARIFICATION` remains. Most pieces already exist and were verified in features 001/002; this
file records the decisions that are new or changed.

## D1 — Closest match, exact first

- **Decision**: `Matcher.closest(text)`: normalize the text; if it equals one of the exact forms of a
  product (catalog name, abbreviation expansions, full-wording variants) return that product; otherwise
  score every product with `rapidfuzz.fuzz.token_sort_ratio` against **all** its forms and return the best.
  **No similarity floor.** Ties go to the first product in Excel order (block, then row). A text that
  normalizes to nothing yields no item.
- **Variants**: `assets/abbreviations.json` `variantes` gets `"7": ["sete"]`, so "7 Linhas", "7 Forças"
  and "7 Giras" also match "sete linhas" and so on, exactly; "s" keeps santo/santa/saude.
- **Rationale**: Constitution IV. The exact-first rule keeps look-alike products ("Abre Caminho" vs
  "Abre C. da Felicidade") apart whenever the customer writes a full name.
- **Known effect** (owner's decision): "abre c. da vitória" with a typo can land on "Abre C. da
  Limpeza", and nonsense lands on some product. The customer reading the list is the only check.
- **Alternatives**: a similarity floor with "não identificado" lines (rejected by the owner); embeddings
  (removed); LLM choosing the product (rejected: the LLM only reads).

## D2 — The chain

`order_chain = extract | match.map | aggregate`, all LCEL Runnables; `render` is a plain function of the
aggregated list. Output of the chain: `[(Product, quantity)]` in Excel order. Removed from the old chain:
embedding, memory, flags, validation, tie-break, text-fidelity check (it served the strict matching; with
closest-match a corrected typo does no harm).

## D3 — Conversation rules

`interpret(text)` normalizes (lowercase, no accents, punctuation to spaces, collapsed spaces) and checks
the **whole** message: ok words `ok, okay, sim, s, confirmo, confirmado, isso, certo, blz, pode, beleza`;
no words `nao, n, cancelar, cancela, errado, negativo`; anything else is an order. `Conversa.responder`:

| Input | Pending order | Result |
|---|---|---|
| order text | any | read → list → new `aguardando` order, the old one becomes `substituido`; reply = list + `ok ou não?` |
| order text, nothing readable | any | reply `SEM_ITENS`; pending kept |
| ok | yes | generate the Excel; success → `confirmado` + file + `CONFIRMADO`; failure → `ERRO_PLANILHA`, still pending |
| ok | no | `ENVIE_PEDIDO`, no file |
| não | yes | `recusado` + `CANCELADO` |
| não | no | `ENVIE_PEDIDO` |

A confirmed order is not pending, so a second "ok" gets `ENVIE_PEDIDO` and no second file.

## D4 — Persistence

One table `pedidos` (see [data-model.md](data-model.md)); `catalog` is kept. The old tables of 001/002
(`aliases`, `runs`, `run_lines`, `memoria_*`) and the `vector` extension are dropped by a **guarded cleanup**
that runs only when those tables exist (their data was demonstration data). `schema.sql` stays idempotent.
`check_database` no longer checks vector dimensions. Each operation is one transaction; replacing the
pending order is one transaction (mark old `substituido` + insert new).

## D5 — Excel timing

The Excel is generated **when the customer says ok** (so a failure can be answered and retried) and is
re-generated on download from the stored items of a `confirmado` order, so it can always be recreated.
The engine returns the file bytes in the reply; the HTTP layer exposes a download URL.

## D6 — Extraction prompt

The prompt asks only for `texto` (as the customer wrote it) and `quantidade` in dozens, converts units
("12 unidades" = 1 dúzia, "meia dúzia" = 0.5), and says that a missing quantity is 1. The `unidade`
field disappears from the schema. One retry on failure is kept; a second failure becomes
`ERRO_LEITURA`.

## D7 — Tests

Kept and adapted: normalize, catalog, export, llm, fakes (server only), db, startup, extract, ptbr
scanner. Rewritten: store, matcher, regression. New: lista, conversa, API. Deleted: validate, alias
learning, memory (write/guard/neighbors/match), reprocess, embeddings, extract examples/fallback of the old
shape, history/memory/ajuda/texto_alterado contracts, fidelity and examples flows.

## D8 — Risks

- Closest-match-always (D1) is deliberate; documented in the spec and the constitution.
- A local 14B model varies between runs (seen in 002): a missed item is not shown at all, since the bot
  never reports doubt. The regression script measures how often the intended product is reached.

## Medição final (2026-11-16)

- Mensagens de regressão (22 arquivos, 49 linhas com produto pretendido): **49/49 = 100%** no produto pretendido, tanto com as extrações gravadas quanto com o modelo local real (`qwen2.5:14b` via Ollama). Formas exatas: 100%.
- Teste completo: 239 testes verdes (Postgres real no Docker). Conversa verificada no navegador: pedido → lista em ordem do Excel → `ok` → link da planilha (200, `.xlsx`).
- Limite conhecido: o modelo local varia entre execuções e a primeira chamada é lenta (carrega o modelo).
