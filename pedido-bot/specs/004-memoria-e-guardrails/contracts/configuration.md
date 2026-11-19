# Contract: configuration (environment variables)

All optional unless noted; invalid numbers fall back to the default.

| Variable | Default | Meaning |
|---|---|---|
| `EMBED_BASE_URL`, `EMBED_MODEL` | none | both set = the memory is on; otherwise the bot behaves as 003 |
| `EMBED_API_KEY` | none | key (environment only; a local Ollama ignores it) |
| `EMBED_DIMENSIONS` | 1024 | vector size, fixed when `apelidos` is created |
| `EMBED_TIMEOUT_SECONDS` | 5 | wait for one embedding call |
| `EMBED_SIMILARITY` | 0.92 | minimum cosine similarity for a nickname match |
| `MAX_LINHAS` | 50 | lines read from one message |
| `MAX_TEXTO_LINHA` | 120 | characters of a line's text |
| `MAX_MENSAGEM` | 2000 | characters of an order message |
| `LIMITE_MSG_POR_MINUTO` | 20 | messages per phone in 60 s |
| `MAX_QTD_PRODUTO` | 1000 | dozens of ONE product in one order |

Startup refuses (Portuguese message) when the `vector` extension cannot be created, or when `apelidos`
already exists with a vector size different from `EMBED_DIMENSIONS`.
