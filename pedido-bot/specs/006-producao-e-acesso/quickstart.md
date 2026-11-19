# Quickstart: validating feature 006

Prerequisites: `docker compose up -d db`; a `.env` with `DATABASE_URL`.

1. `uv run pytest` → all green.
2. **Migrations**: `uv run python -m pedido.migrate --status` lists `0001` and `0002`; `uv run python -m
   pedido.migrate` applies what is pending; running it again changes nothing.
3. **Local run** (no keys): `uv run python -m pedido` starts with a warning; the page works as before.
4. **With keys**: `API_KEYS="teste:conversa+modelo:$(python3 -c 'import secrets;print(secrets.token_urlsafe(32))')"`;
   call `/api/mensagem` with no key (401), a wrong key (401) and the right one (200); the model routes with a key
   that has only `conversa` (403).
5. **Production mode**: `ENVIRONMENT=producao PORT=9000` with the keys: `/`, `/docs` and `/openapi.json` answer
   404; the process listens on all addresses; without `API_KEYS` it refuses to start.
6. **Health**: `curl localhost:9000/saude` → `{"status":"ok"}`; stop the database → 503.
7. **Limits**: send 201 messages from one conversation (the 201st gets the daily-limit sentence); 121 requests
   in a minute with one key (the 121st gets 429).
8. **Embeddings**: with `EMBED_SEND_DIMENSIONS=true` the request carries `dimensions`; `uv run python
   scripts/apelidos.py --reindexar` prints the totals.
9. **Container**: `docker build -t pedido-bot .` and run it with the variables; `GET /saude` answers.
