# Contract: configuration and startup

Everything is configured through environment variables (a `.env.example` documents them, with no
secrets). **Keys and secrets are only read from the environment; they never appear in responses,
logs shown to the user, or the database.**

## Variables

| Variable | Required | Default | Meaning |
|---|---|---|---|
| `DATABASE_URL` | **yes** | — | Postgres connection string, e.g. `postgresql://pedido:pedido@localhost:5433/pedido`. Moving to Supabase = changing this value only. |
| `LLM_PROVIDER` | no | `anthropic` | `anthropic` or `openai_compatible` |
| `LLM_MODEL` | for `openai_compatible` | `claude-sonnet-5-5` for `anthropic` | model name |
| `LLM_BASE_URL` | for `openai_compatible` | — | service address, e.g. `https://ollama.com/v1` |
| `LLM_API_KEY` | for `openai_compatible` | — | key for the OpenAI-compatible service |
| `ANTHROPIC_API_KEY` | for `anthropic` | — | key for the Claude service |
| `LLM_STRUCTURED_METHOD` | no | `json_schema` | `json_schema`, `function_calling` or `json_mode` (for services lacking schema support) |
| `EMBED_BASE_URL` | for memory | — | embeddings service address (OpenAI-style `/v1/embeddings`) |
| `EMBED_MODEL` | for memory | — | embedding model name |
| `EMBED_API_KEY` | for memory | — | key for the embeddings service |
| `EMBED_DIMENSIONS` | no | `1024` | vector size; **fixed when the memory tables are created** |
| `EMBED_TIMEOUT_SECONDS` | no | `5` | longest wait on the embeddings service per call |

The embedder counts as *configured* only when `EMBED_BASE_URL`, `EMBED_MODEL` and `EMBED_API_KEY` are
all set. If none is set, memory features are simply inactive and the tool behaves as in 001. If some
but not all are set, startup refuses (below).

Matching and memory thresholds (`MEMORY_NEIGHBORS`=5, `MEMORY_MIN_SIMILARITY`=0.82,
`MEMORY_PRESELECT_SIMILARITY`=0.90, `MESSAGE_EXAMPLES`=3, `MESSAGE_MIN_SIMILARITY`=0.75) are
constants in `config.py`, tuned on the regression set — not environment variables.

## Startup behavior (`python -m pedido` or `uvicorn pedido.web.app:app`)

The tool does not start, prints one of these messages (Portuguese) and exits with code 1:

| Situation | Message |
|---|---|
| `DATABASE_URL` missing | "O banco de dados não está configurado. Defina a variável DATABASE_URL com o endereço do Postgres (veja o arquivo .env.example)." |
| cannot connect (5 s) | "Não foi possível conectar ao banco de dados. Confira se o Postgres está rodando (docker compose up -d db) e se DATABASE_URL está correta." |
| pgvector unavailable | "O banco de dados não tem a extensão pgvector. Use uma imagem ou serviço com pgvector (veja o docker-compose.yml)." |
| dimension mismatch | "O banco foi criado para vetores de {atual} dimensões, mas EMBED_DIMENSIONS está em {configurado}. Use o mesmo valor ou recrie as tabelas de memória." |
| partial embeddings config | "A configuração de embeddings está incompleta: falta {variáveis}." |
| invalid `LLM_PROVIDER` | "LLM_PROVIDER deve ser 'anthropic' ou 'openai_compatible'." |

A missing LLM key or address is **not** a startup error: the first analysis fails with the 001
message and the user fills the table by hand (spec FR-008).
