# Pesquisa

- **Proxy no backend** (decisão): o navegador só fala com o estoque. Racional: sem CORS, porta do robô fechada ao navegador, futura chave de API fica no servidor. Alternativa descartada: chamar o robô direto do Angular.
- **fetch global + AbortController**: sem dependência nova (Node 20). Timeout 90 s porque o modelo local é lento; configurável por `PEDIDO_BOT_TIMEOUT_MS`.
- **Corpo binário**: parsers `application/octet-stream` e mime do xlsx como Buffer, limite 6 MB.
- **Identificador de conversa**: UUID por navegador em localStorage (try/catch); enviado como `conversaId`, repassado como `telefone`.
- **Erros**: robô inalcançável/timeout → 503 `{ error }` (formato lido pelo interceptor). Erros 422/413 do robô passam sem alteração `{erro, mensagem}`.
- **Download**: link direto para `/api/pedido-bot/...` (o backend faz streaming do bot com o mesmo Content-Disposition).
