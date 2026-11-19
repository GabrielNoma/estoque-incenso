# Contract: environment variables

| Variable | Default | Meaning |
|---|---|---|
| `ENVIRONMENT` | (local) | `producao` switches on the production rules |
| `PORT` | 10000 in production | listening port (production); locally 8000 |
| `API_KEYS` | none | `name:scopes:key,...`; required in production; keys of 32+ characters |
| `DATABASE_URL` | none | required |
| `MIGRATE_ON_START` | false | local convenience only: apply pending migrations at start |
| `LLM_MAX_TOKENS` | 4096 | maximum output of every language model call |
| `LIMITE_DIARIO_CONVERSA` | 200 | messages per conversation per day |
| `LIMITE_REQ_POR_CHAVE` | 120 | requests per key per minute |
| `MAX_LLM_CONCORRENTES` | 4 | simultaneous language model calls |
| `ESPERA_LLM_SEGUNDOS` | 20 | how long a message waits for a slot |
| `MAX_CORPO_MENSAGEM_KB` | 64 | message request body limit |
| `EMBED_BASE_URL`, `EMBED_MODEL`, `EMBED_API_KEY` | none | hosted embeddings (OpenAI-compatible) |
| `EMBED_DIMENSIONS` | 1024 | vector size of the memory table |
| `EMBED_SEND_DIMENSIONS` | false | send the size to the service as `dimensions` |
| `LLM_*`, `ANTHROPIC_API_KEY`, `MAX_*`, `LIMITE_MSG_POR_MINUTO` | as before | unchanged |
