# Tasks: Tela Pedidos (003-pedido-bot-chat)

Testes primeiro (ver falhar, depois implementar). Formato: `- [ ] ID [P] [Story] descrição + arquivo`.

## Phase 1: Setup
- [x] T001 Adicionar `PEDIDO_BOT_URL` e `PEDIDO_BOT_TIMEOUT_MS` em `backend/.env.example`
- [x] T002 Adicionar `tests/pedidoBot.test.js` ao script `test` em `backend/package.json`

## Phase 2: Fundação (proxy backend, bloqueia as histórias)
- [x] T003 Escrever `backend/tests/pedidoBot.test.js` com bot falso (http.createServer) cobrindo: mensagem + reescrita da url, planilha, modelo GET, modelo POST (corpo bruto + X-Nome-Arquivo, passagem de 422/413/200), info, 400 sem campos, 503 bot fora, 503 timeout; ver falhar
- [x] T004 Implementar `backend/src/routes/pedidoBot.js` (chamarBot com fetch+AbortController, parsers Buffer, limite 6 MB) e registrar em `backend/app.js`; testes passam

## Phase 3: US1 Chat (P1)
- [x] T005 [US1] Escrever `frontend/src/app/features/pedido-bot/pedido-bot.service.spec.ts` (enviar mensagem, conversaId persistente, URLs) e ver falhar
- [x] T006 [US1] Escrever `pedido-bot.component.spec.ts` (balões, digitando, desabilitar, link Baixar planilha) e ver falhar
- [x] T007 [US1] Implementar `pedido-bot.service.ts` e `pedido-bot.component.ts`; rota `/pedidos` em `app.routes.ts`; item "Pedidos" em `app.component.ts`

## Phase 4: US2/US3 Modelo (P2)
- [x] T008 [US2][US3] Estender specs do serviço/componente: exportar, importar (X-Nome-Arquivo codificado), info, erro 422 exibe mensagem
- [x] T009 [US2][US3] Implementar botões Exportar/Importar, diálogo de confirmação, diálogo de resumo, linha de info do modelo

## Phase 5: Polimento e verificação
- [x] T010 Atualizar CLAUDE.md (Recent Changes) com a feature
- [x] T011 `npm test` backend (56/56) e `ng build` ok; `ng test` NÃO executado (sem Chrome na máquina)
- [x] T012 Verificação no navegador (pedido, ok, download, exportar, importar com produto novo, restaurar modelo original, mobile/desktop)
