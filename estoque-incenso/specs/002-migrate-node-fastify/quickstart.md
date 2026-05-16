# Quickstart: Migração para Node.js + Fastify + Deploy Render/Supabase

## Arquivos criados/modificados

| Arquivo | Mudança |
|---------|---------|
| `backend/src/routes/funcionarias.js` | 4 endpoints (GET/POST/PUT/PATCH) |
| `backend/src/routes/registros.js` | 3 endpoints (GET/PUT/DELETE) |
| `backend/src/routes/exportacao.js` | 1 endpoint (GET /excel) |
| `backend/src/plugins/db.js` | Pool pg via `fastify.decorate` |
| `backend/src/plugins/cors.js` | @fastify/cors configurado |
| `backend/src/plugins/static.js` | @fastify/static → frontend/dist/browser |
| `backend/src/db/schema.sql` | DDL completo (substitui EF Core migrations) |
| `backend/app.js` | Instância Fastify + plugins + rotas |
| `backend/server.js` | Entrypoint: `app.listen(PORT)` |
| `backend/.env.example` | Template de variáveis de ambiente |
| `backend/package.json` | Node.js 20, dependências Fastify/pg/ExcelJS |
| `.github/workflows/deploy.yml` | CI/CD: build Angular → Deploy Hook Render |

## Sem mudanças em

- Frontend Angular (`frontend/`) — nenhum arquivo alterado
- Schema PostgreSQL — tabelas idênticas
- Contratos de API — mesmos paths, métodos e payloads

## Como executar localmente

```bash
# 1. Configurar banco de dados
psql -U postgres -c "CREATE DATABASE estoque_incenso;"
psql -U postgres -d estoque_incenso -f backend/src/db/schema.sql

# 2. Configurar variáveis de ambiente
cd backend
cp .env.example .env
# editar .env: DATABASE_URL=postgresql://postgres:senha@localhost:5432/estoque_incenso

# 3. Instalar dependências e iniciar
npm install
node server.js
# → Server running on http://localhost:3000

# 4. (Opcional) Compilar e servir frontend
cd ../frontend
npm run build
# Fastify já serve ../frontend/dist/browser em localhost:3000
```

## Verificação manual (cenários de aceite)

| # | Ação | Resultado esperado |
|---|------|--------------------|
| 1 | `GET /api/funcionarias` | JSON array de funcionárias ativas |
| 2 | `POST /api/funcionarias` `{ "nome": "Teste" }` | Status 201, objeto com id |
| 3 | `GET /api/registros?ano=2026&mes=5` | Grade mensal com funcionárias e registros |
| 4 | `PUT /api/registros` `{ "funcionariaId":1, "data":"2026-05-13", "quantidade":50, ... }` | Status 200, registro salvo |
| 5 | `DELETE /api/registros/1` | Status 204, célula limpa |
| 6 | `GET /api/exportacao/excel?ano=2026&mes=5` | Download `producao_2026_05.xlsx` com abas Produção e Faltas |
| 7 | Abrir `http://localhost:3000` no browser | App Angular carrega normalmente |
| 8 | Push para `main` no GitHub | GitHub Actions roda, Render recebe Deploy Hook, app atualiza em produção |

## Deploy em produção

### 1. Supabase
1. Criar projeto gratuito em supabase.com
2. Copiar a connection string `DATABASE_URL` (formato `postgresql://...`)
3. Abrir SQL Editor no dashboard e colar + executar `backend/src/db/schema.sql`

### 2. Render
1. Criar Web Service gratuito apontando para o repositório
2. Build Command: `cd frontend && npm install && npm run build && cd ../backend && npm install`
3. Start Command: `node backend/server.js`
4. Configurar `DATABASE_URL` nas Environment Variables
5. Copiar Deploy Hook URL (Settings → Deploy Hook)

### 3. GitHub Actions
1. Adicionar `RENDER_DEPLOY_HOOK_URL` nos Secrets do repositório
2. Push para `main` → pipeline roda automaticamente
