# Contrato (estoque → navegador)
- POST /api/pedido-bot/mensagem `{conversaId, texto}` → 200 `{resposta, arquivo|null}`; arquivo.url reescrita para `/api/pedido-bot/planilha/{id}`; 400 `{error}` se faltar campo; 503 `{error}`.
- GET /api/pedido-bot/planilha/:id → xlsx (Content-Disposition do robô); erros do robô repassados.
- GET /api/pedido-bot/modelo → xlsx `modelo-pedido.xlsx`.
- POST /api/pedido-bot/modelo (corpo xlsx bruto, header X-Nome-Arquivo) → status/JSON do robô (200 | 422 | 413).
- GET /api/pedido-bot/modelo/info → JSON do robô.
- Robô indisponível / timeout → 503 `{ "error": "O serviço de pedidos não está disponível. Tente novamente em instantes." }`.
