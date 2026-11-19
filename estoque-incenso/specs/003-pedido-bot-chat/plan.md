# Plano de Implementação: Tela Pedidos (003-pedido-bot-chat)

**Spec**: [spec.md](spec.md)

## Contexto técnico
- Backend: Node 20, Fastify 5, CommonJS; `fetch` global (sem novas dependências); testes `node --test` com bot falso (`http.createServer`).
- Frontend: Angular 17 standalone + Angular Material; testes Karma/Jasmine.
- Integração: API HTTP do robô em `PEDIDO_BOT_URL` (padrão `http://127.0.0.1:8000`). Sem banco novo.
- Timeout do proxy: `PEDIDO_BOT_TIMEOUT_MS` (padrão 90000), configurável para testes.

## Verificação da Constituição
- I Simplicidade: um plugin de rotas pequeno, um serviço e um componente; sem abstrações novas. OK.
- II SOLID/DRY: função única `chamarBot` (fetch + timeout + 503) reutilizada por todas as rotas. OK.
- III Observabilidade: erros do robô (indisponível/timeout) logados em nível warn/error sem texto de pedido nem id de conversa. OK.

## Estrutura
```text
backend/src/routes/pedidoBot.js        # proxy (novo)
backend/app.js                         # registra rota (prefixo /api)
backend/tests/pedidoBot.test.js        # novo, bot falso
backend/package.json, .env.example     # script de teste e PEDIDO_BOT_URL
frontend/src/app/features/pedido-bot/  # pedido-bot.service.ts, pedido-bot.component.ts, dialogos, specs
frontend/src/app/app.routes.ts, app.component.ts
```

## Decisões
Ver [research.md](research.md), [data-model.md](data-model.md), [contracts/api.md](contracts/api.md), [quickstart.md](quickstart.md).
