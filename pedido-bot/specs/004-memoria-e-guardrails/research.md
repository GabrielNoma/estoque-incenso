# Research: Memória silenciosa de apelidos e guardrails

No `NEEDS CLARIFICATION` remains. Decisions new to this feature:

## D1 — What a nickname is and when it applies

A row of `apelidos` is the pair (normalized wording, product). It **applies** when `status = 'ativo'`,
`positivos >= 2` and `positivos > negativos`. Exact wordings of the product never create rows (the
catalog already knows them). A line that was matched by closest product or by a nickname and then
confirmed adds a positive. Several nicknames can apply to the same text only through different products:
the one with the highest `positivos - negativos` wins, then the first in Excel order.

## D2 — Signals and the moment they are written

- **ok** → for each matched line of the order: upsert the pair, `positivos + 1`, with the embedding.
- **não / substituído** → for each line whose pair already exists: `negativos + 1`. No row is created or
  deleted.
- Each transition writes once (the engine triggers it right after the state change), after the reply is
  built, by a single background worker (`ThreadPoolExecutor(max_workers=1)`), so the reply never waits.
  Tests inject an inline executor. A crash before the write only loses one signal (acceptable: silent).

## D3 — Embeddings

`embeddings.py`: `Embedder.embed(text) -> list[float]` over `langchain_openai.OpenAIEmbeddings`
(`check_embedding_ctx_length=False`, required for Ollama), `base_url`, `model`, `api_key`, `timeout`.
Configured when `EMBED_BASE_URL` and `EMBED_MODEL` exist; otherwise `None` and the bot is exactly 003.
Dimension from `EMBED_DIMENSIONS` (default 1024, bge-m3). A vector of another size is discarded. Lookup
cost control: no embedding call when no nickname exists for the model, and after the first failure in a
message the embedder is skipped for the rest of that message.

## D4 — Database

`create extension if not exists vector`; table `apelidos` with `embedding vector(N)` where N is the
configured dimension, built at startup (the dimension is fixed at creation; a different later value
raises a Portuguese `StartupError` naming the stored size). `embedding` is nullable (a wording learned
while the embedder was down still works by exact text). `modelo` stores the embedder's model name;
similarity searches filter `modelo = current`; exact-text lookup ignores the model. The legacy cleanup
of 003 stops dropping the `vector` extension. `pedidos` gains `linhas jsonb` (the matched lines: wording,
quantity, product id), the source for the signals.

## D5 — Similarity threshold (calibrated with the real `bge-m3`, 2026-11-16)

`EMBED_SIMILARITY` default **0.92** cosine similarity (`1 - (embedding <=> query)`), high to favor
precision. Measured with the real model on normalized wordings:

| Same product (should match) | cosine |
|---|---|
| abre c felicidade ~ abre c da felicidade | 0.980 |
| abre camino ~ abre caminho | 0.943 |
| descarrego completto ~ descarrego completo | 0.936 |
| sao jorge ~ são jorge guerreiro | 0.805 |
| arruda velha ~ arruda | 0.818 |
| 7 linhas ~ setes linhas | 0.787 |
| alecrim ~ alecrin | 0.738 |

| Different products (must NOT match) | cosine |
|---|---|
| abre caminho ~ abre c da felicidade | **0.850** |
| ogum ~ oxum | 0.697 |
| sao jorge ~ sao miguel | 0.682 |
| 7 linhas ~ 7 forcas | 0.641 |

The look-alike pair "Abre Caminho" / "Abre C. da Felicidade" already reaches 0.85, so the first guess of
0.85 was too low; 0.92 keeps the typos of the same name (0.93 to 1.00) and rejects every look-alike
measured. Short or loose variants (0.74 to 0.82) are intentionally left to the closest-product step.

## D6 — Guardrails

- **Prompt**: the customer's message is placed between fixed delimiters with an explicit sentence that any
  instruction inside is data to read, never to follow. The memory never enters the prompt.
- **Output validation** (`validar_linhas`): at most `MAX_LINHAS` (50) lines, text trimmed and at most
  `MAX_TEXTO_LINHA` (120) characters (longer lines are dropped), `quantidade` must be a finite number
  (not bool, not NaN) greater than zero; invalid lines are dropped silently.
- **Quantity cap**: after summing, any product above `MAX_QTD_PRODUTO` (1000) dozens → reply
  `QUANTIDADE_ALTA`, nothing stored, the pending order kept; exactly 1000 is accepted.
- **Size and rate**: `MAX_MENSAGEM` (2000) characters checked before the model is called;
  `LIMITE_MSG_POR_MINUTO` (20) per phone in a sliding 60-second window kept in memory (injected clock for
  tests). The size limit applies to order texts; the rate limit to every message.
- **No path for model text**: the engine only reads the model's `{texto, quantidade}`; every customer
  sentence is a constant of `messages.py`.
- **Logs**: `guardrails.registrar(tipo)` logs `guardrail=<tipo>` only (types: `mensagem_longa`,
  `taxa`, `quantidade_alta`, `linhas_invalidas`, `linhas_demais`).

## D7 — Order of checks in `Conversa.responder`

rate limit → read the reply (ok/não/order) → for an order: size → model → validation → match (with
nickname lookup) → aggregate → quantity cap → store and render. ok and não are unaffected by the size
check. Every refusal is one constant sentence and keeps the pending order.

## D8 — Script

`scripts/apelidos.py` (Portuguese output): no argument lists `id | texto | produto | +positivos |
-negativos | status | aplica`; `--desativar ID` / `--ativar ID` change `status`; unknown id prints a
Portuguese message and changes nothing. It reads `DATABASE_URL` from the environment.

## D9 — What does not change

Replies, the Excel, the chat page, the HTTP contract, the failure replies and the state machine of 003.

## Medição final (2026-11-16)

- 431 testes verdes (Postgres com pgvector real; stubs e servidor falso de chat e embeddings).
- Regressão com o modelo local real (`qwen2.5:14b`): **49/49 = 100%** no produto pretendido; formas exatas 100%.
- Aprendizado de ponta a ponta com o Ollama real: duas confirmações de "abre c felicidade" criaram o apelido (2 positivos, modelo `bge-m3`), sem nenhuma mudança no que o cliente vê.
- Guardrails com o modelo real: mensagem com instruções → resposta neutra sem itens; 5000 dz → `QUANTIDADE_ALTA`; texto de 2500 caracteres → `MENSAGEM_LONGA` sem chamar o modelo; 25 mensagens seguidas de um número → 20 processadas e 5 com `MUITAS_MENSAGENS`; o log tem só `guardrail=<tipo>`.
- **Limite conhecido do modelo local**: "1000 dz de ogum" foi lido como 100 dz. Um erro de leitura abaixo do limite não é pego por guardrail; a defesa é o cliente conferir a lista (`ok ou não?`). Um modelo maior ou o Claude reduz esse tipo de erro.
- Porta do banco do bot: 5434 (a 5433 é do `estoque-incenso-db`, outro projeto do usuário).
