# Requirement for the stock system repository (estoque-incenso) — not built here

1. Add two environment variables to the stock **backend**: `PEDIDO_BOT_URL` (the bot's address; a private
   address when the platform offers one) and `PEDIDO_BOT_API_KEY` (a key of the bot with the scopes
   `conversa`, `modelo` and `historico`; the last one is only for the order history screen).
2. In `backend/src/routes/pedidoBot.js`, send the header `Authorization: Bearer ${PEDIDO_BOT_API_KEY}` on every call to
   the bot. The key never reaches the browser and is never logged.
3. Map the new bot errors for the screen: 401/403 → a Portuguese "serviço de pedidos não autorizado" notice
   (a configuration problem), 429 → ask to wait, 413 → the model file is too large.
4. Because the import of the model replaces it for everyone, restrict that button in production (for example
   an access PIN checked by the stock backend); anyone holding a key with the `modelo` scope can replace it.
5. The conversation id sent by the screen stays an anonymous per-browser id; the daily limit of 200 messages
   is per id.
