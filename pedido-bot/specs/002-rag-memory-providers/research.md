# Research: Banco único, serviços de IA configuráveis e memória de pedidos

All Technical Context items are resolved; no `NEEDS CLARIFICATION` remains. Two items can only be
confirmed with real credentials and are listed under **Open verification** at the end.

## Verified in an isolated environment (2026-10-23)

Installed with `uv run --no-project --python 3.11` and inspected: `langchain-openai` 1.7.2,
`psycopg` 3.3.6, `pgvector` 0.5.1.
- `OpenAIEmbeddings` accepts `base_url`, `api_key`, `model`, `dimensions`, `timeout`, `max_retries`
  and **`check_embedding_ctx_length`**.
- `ChatOpenAI.with_structured_output(method=...)` supports `json_schema`, `json_mode` and
  `function_calling`.
- `pgvector.psycopg` exposes `register_vector`.

## D1 — Database access

- **Decision**: `psycopg` 3, **one connection per operation**, `prepare_threshold=None`, with
  `pgvector.psycopg.register_vector` on each connection. No ORM, no pool, no migration framework; a
  single idempotent `schema.sql` is applied at startup.
- **Rationale**: one user and small volume; per-operation connections work unchanged behind
  Supabase's transaction pooler (which does not support prepared statements); fewer moving parts
  (Constitution VII).
- **Alternatives**: SQLAlchemy/Alembic (heavy for 6 tables); `psycopg_pool` (a future optimization if
  the hosted latency per connection hurts); `asyncpg` (the app code is synchronous).

## D2 — Schema, dimension and index

- **Decision**: schema `pedido`; `create extension if not exists vector`; tables from
  [data-model.md](data-model.md); `schema.sql` is rendered with the embedding dimension
  `EMBED_DIMENSIONS` (default **1024**). At startup, if `pedido.memoria_*` already exist with a
  different dimension, the app **refuses to start** with a pt-BR message (changing the model's
  dimension means recreating the memory tables and reprocessing). Index: HNSW with
  `vector_cosine_ops`.
- **Rationale**: the dimension is fixed per column; guarding it avoids silent insert errors later.
  HNSW is the index Supabase recommends, supported up to 2,000 dimensions
  ([Supabase doc](https://supabase.com/docs/guides/troubleshooting/increase-vector-lookup-speeds-by-applying-an-hsnw-index-ohLHUM)).
- **Supabase later**: enable RLS on every table with no policies (the REST API then exposes nothing);
  the direct/pooler connection string goes in `DATABASE_URL`; tables stay in schema `pedido`.
- **Alternatives**: IVFFlat (needs training data); an unindexed scan (fine at this scale, but the
  index costs nothing and the hosted future benefits).

## D3 — LLM provider adapters

- **Decision**: `llm.build_chat_model()` reads `LLM_PROVIDER`:
  - `anthropic` → `ChatAnthropic` as today (`LLM_MODEL`, `ANTHROPIC_API_KEY`).
  - `openai_compatible` → `ChatOpenAI(base_url=LLM_BASE_URL, api_key=LLM_API_KEY, model=LLM_MODEL,
    temperature=0)`; structured output via `method="json_schema"`, switchable with
    `LLM_STRUCTURED_METHOD=function_calling|json_mode` for services that lack schema support.
  Built lazily (the app starts without a key); a missing key or address surfaces as the existing
  pt-BR analysis failure with the empty manual table (001 behavior).
- **Rationale**: one adapter reaches Ollama's hosted endpoint (`https://ollama.com/v1`,
  [doc](https://pydantic.dev/docs/ai/models/ollama/)) and any OpenAI-style service; the stages already
  take the chat model as an injected dependency.
- **Alternatives**: `langchain-ollama` (its use against the hosted endpoint is unconfirmed); one
  adapter per vendor (more code, no benefit).

## D4 — Embeddings

- **Decision**: `embeddings.OpenAICompatibleEmbedder` wraps `OpenAIEmbeddings(base_url=EMBED_BASE_URL,
  api_key=EMBED_API_KEY, model=EMBED_MODEL, dimensions=EMBED_DIMENSIONS if set,
  check_embedding_ctx_length=False, timeout=EMBED_TIMEOUT_SECONDS, max_retries=1)`.
  `check_embedding_ctx_length=False` is required for non-OpenAI servers because the default sends
  token ids instead of text. `SafeEmbedder` wraps any embedder: **any failure, timeout or missing
  configuration returns `None`** (never raises), logging only the error class, never keys or text.
  `embed_batch(texts)` is one call.
- **Rationale**: Constitution V (injected, batched) and VI (a failed call must not lose an approval);
  Claude has no embeddings API, so a separate service is configured.
- **Alternatives**: a local Ollama embedder (the user chose an API); embedding inside the matcher
  per line (many calls, slow).

## D5 — Memory help when matching (the guard)

Embedding similarity between "abre caminho" and "abre caminho da felicidade" is high, so memory must
be **advisory with its own look-alike guard**:

- **Retrieval**: cosine nearest `MEMORY_NEIGHBORS`=5 remembered lines with the **same
  `modelo_embedding`** and similarity ≥ `MEMORY_MIN_SIMILARITY`=0.82; deduplicated by product
  (best similarity), ties broken by most recent confirmation.
- **Use**: only for lines that already need review (exact/alias/safe-fuzzy are decided as in 001).
  Remembered products join the candidate list; ranking = best of the fuzzy score and `similarity×100`;
  at most 3 candidates are shown, as in 001.
- **Pre-selection** of a remembered product requires similarity ≥ `MEMORY_PRESELECT_SIMILARITY`=0.90 and
  the **guard**: the product's first word is unique in the catalog, **or** the query and the remembered
  wording are *token-compatible* (same number of tokens and, token by token after sorting, each pair
  scores ≥ 80 — i.e., a typo-level variant). So a remembered "abre caminho" never pre-selects "Abre
  Caminho" for "abre caminho da felicidade" (extra token, family product), while a typo "abre camiho"
  may. A remembered product that fails the guard may still appear as a lower candidate, never first by
  memory.
- **Never auto-accept**: help sets `motivo="memoria"` (label "parecido com um pedido anterior"),
  `precisa_revisao=True`, and the user must confirm (Constitution III/IV, FR-015/FR-016).
- **Unavailable memory/embedder**: the step returns the 001 result unchanged.

## D6 — Writing the memory at approval

- **Decision**: approval is committed first, in its own transaction. Afterwards `memory.write_for_run`
  runs in a **separate step**: for each final line with a non-empty written text and a product
  (including auto-accepted lines the user approved) it upserts a `memoria_linhas` row keyed by
  `(texto_normalizado, produto_id, modelo_embedding)` (refreshing `confirmado_em`); it also writes one
  `memoria_mensagens` row (message + final lines as JSON). Texts are embedded in **one batch**. If the
  embedder returns `None`, rows are written with `embedding = NULL` and the run's `memoria_estado` is
  `pendente`; otherwise `completa`. Removed lines, unconfirmed suggestions and lines without text are
  never written.
- **Embedder not configured at approval**: nothing is written and `memoria_estado` stays
  `nao_aplicavel`; the reprocess command later **backfills** approved runs in that state, so enabling
  the embeddings later still teaches the system from past orders.
- **Reprocess**: `python -m pedido.reprocess` finds rows with `embedding IS NULL` or a different
  `modelo_embedding` than configured, embeds them in batches, updates them, and sets each affected
  run to `completa` when none of its rows is pending. Idempotent; safe to interrupt.
- **Rationale**: Constitution VI; separating transactions guarantees an embedder failure cannot roll
  back or delay an approval beyond `EMBED_TIMEOUT_SECONDS`.

## D7 — Few-shot examples for extraction

- **Decision**: before extraction, the message is embedded (truncated to 2,000 characters for the
  vector only); up to `MESSAGE_EXAMPLES`=3 remembered messages with similarity ≥
  `MESSAGE_MIN_SIMILARITY`=0.75 (same model) are added to the pt-BR prompt as "Exemplos de mensagens
  anteriores e como foram lidas" with their final lines (written text, quantity, unit). No examples →
  the prompt is exactly the 001 prompt.
- **Rationale**: lets the model pick up each customer's habits; examples come only from approved data.

## D8 — Chain wiring

`proposal = embed_message | retrieve_examples | extract(examples) | embed_lines (one batch) |
match.map (with memory help) | validate`. Every memory step catches failure and degrades to 001
behavior; the approval chain is `save_corrections` (aliases, as in 001) then `write_memory` (D6).
Embedding calls per proposal: at most two (message; the line texts in one batch).

## D9 — Startup and configuration errors

- **Decision**: `db.check_database(url)` (connect with a 5 s timeout, `create extension` / schema,
  dimension check) raises `StartupError` carrying a pt-BR message from `messages.py`. `python -m
  pedido` validates configuration, prints the message and exits with code 1, or starts the server.
  `uvicorn pedido.web.app:app` also fails with the same `StartupError`. Running-time database failures
  become the pt-BR `erro_banco` response (503), never a half-saved order (each approval is one
  transaction).
- **Rationale**: FR-003/FR-004 (spec), SC-005.

## D10 — Test strategy (Constitution II)

- **Real database**: `docker-compose.yml` runs `pgvector/pgvector:pg16` on port 5433. A session
  fixture creates the test database `pedido_test`, applies `schema.sql`, and `TRUNCATE ... RESTART
  IDENTITY CASCADE` runs before each test. If Postgres is unreachable, the fixture **fails with a
  clear instruction** (`docker compose up -d db`); it never silently skips.
- **FakeEmbedder** (`tests/fakes.py`): deterministic, no network; hashes tokens into a
  `EMBED_DIMENSIONS`-sized vector and L2-normalizes, so cosine reflects word overlap; accepts explicit
  per-text overrides to simulate semantic neighbors; can be told to fail or time out.
- **Fake OpenAI-compatible server** (`tests/fakes.py`): a tiny FastAPI app served on a random local
  port exposing `/v1/chat/completions` and `/v1/embeddings`; tests assert the request (path, bearer
  key, model, `input` list, JSON schema) and the parsing of the response, for the chat adapter and the
  embedder.
- **Regression**: the 179 tests of 001 are migrated to the new `Store`/`create_app` signatures. A new
  fixture `tests/fixtures/memoria/` holds confirmed lines used to measure SC-004 (baseline 83% = 5 of
  the 6 flagged lines with an expected candidate have it first in 001).

## D11 — Local setup facts (this machine)

Docker CLI is installed (`/usr/local/bin/docker`) but the **Docker Desktop daemon was not running**
when checked; `psql`/Supabase CLI are not installed (not needed: the app and tests use `psycopg`).
Starting Docker Desktop is a prerequisite for the database tests.

## Open verification (needs real credentials; not blockers for building)

- **O1 — Structured output on a hosted OpenAI-compatible model**: whether the service honors
  `json_schema`. The adapter supports `function_calling`/`json_mode` through `LLM_STRUCTURED_METHOD`;
  measure with `scripts/run_regression_real.py --provider ... --model ...`.
- **O2 — Hosted embeddings**: no source confirmed that Ollama's hosted service offers embeddings; the
  embedder is configured separately from the LLM so any OpenAI-style embeddings service can be used.

## Memory threshold sweep (T060, 2026-10-24)

Swept `MEMORY_MIN_SIMILARITY` ∈ {0.70, 0.78, 0.82, 0.86} × `MEMORY_PRESELECT_SIMILARITY` ∈ {0.85, 0.90, 0.95}
with a remembered neighbor **injected** at similarity 0.85 / 0.92 / 1.00 for the 6 flagged regression
lines, and at 0.85 / 0.92 / 0.99 / 1.00 for the 2 look-alike traps (`tests/fixtures/memoria`).

| min | preselect | first suggestion correct @0.85 | @0.92 | @1.00 | look-alike traps violated |
|---|---|---|---|---|---|
| 0.70–0.82 | 0.85–0.95 | 100% | 100% | 100% | **0** at every similarity |
| 0.86 | 0.85–0.95 | 83% (the hit is below the minimum, so ignored) | 100% | 100% | **0** at every similarity |

- **The safety does not depend on the thresholds**: no combination pre-selected a look-alike product,
  and memory never accepted a line, at any similarity. It comes from the look-alike guard (first word
  unique, or typo-level token compatibility) and from `precisa_revisao` always being true.
- Thresholds only decide **when** memory acts. **Decision: keep 0.82 / 0.90 / 0.75** (the plan's values).
- **Caveat**: the similarity values are injected, because the real distribution depends on the embedding
  model and cannot be known offline. With a real service, measure with
  `scripts/run_regression_real.py --memory` (SC-004: first suggestion correct with and without memory) and
  re-run this sweep if the real similarities fall outside 0.82–1.00. Run against the *word-hash* fake
  embedder the script reports 5/6 with and without memory, as expected: that fake cannot see that
  "sete linhas" resembles "sete linha".

## First run with real local models (2026-10-24: Ollama 0.40.10, `qwen2.5:14b` + `bge-m3`)

Chat and embeddings both went through the app's OpenAI-compatible adapters (`LLM_BASE_URL` and
`EMBED_BASE_URL` = `http://localhost:11434/v1`), so this also validates research D3/D4 against a real server.

| Measurement | Result |
|---|---|
| Regression, 22 messages, 49 lines (`run_regression_real.py --real`) | **94% (46/49)** right without an edit; **0** wrong auto-accepts; **0** lines missing review. About 2 min 30 s in total (≈ 7 s per message) |
| `bge-m3` vector size | **1024**, equal to the database default; no configuration needed |
| `bge-m3` similarity "abre caminho" × "abre caminho da felicidade" | **0.85**: above `MEMORY_MIN_SIMILARITY`, so this look-alike pair is exactly what the guard exists for (it is blocked) |
| SC-004 with the real embeddings (`--memory`) | first suggestion correct **5/6 (83%) without memory → 6/6 (100%) with memory** (a small fixture of 6 lines whose wordings are typo-level variants; not a proof for real customers) |

**Findings**
1. **The model corrected a customer's typo** ("quebra mau olhdo" → "quebra mau olhado") in 1 of 51 lines. That turned
   an unreviewed guess into an *exact* match and bypassed the strict matching. Fix (tests first, any model):
   a returned text must be **literally in the customer's message** (ignoring case, accents and punctuation);
   otherwise the line gets the flag `texto_alterado` ("Texto diferente do original"), an automatic match is
   downgraded to `motivo = "texto_alterado"` with `precisa_revisao`, and the extraction prompt now says to copy
   the text, typos included. Regression after the fix: 0 wrong auto-accepts.
2. **A 14B local model varies between runs even with temperature 0**: it missed a different message each time
   ("36 unidades de arruda" once, "1 dz de cada" the next). A missed line is safe (the table can be completed by
   hand) but costs the user a step.
3. **Cold start**: the first embedding call after the model was unloaded took longer than the 5 s limit, and the
   app (by design) then skipped the memory. With a local Ollama set `EMBED_TIMEOUT_SECONDS=30` or higher, or keep
   the model loaded. Ollama unloads idle models after 5 minutes by default.
