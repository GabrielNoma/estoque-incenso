# Research: Migração para Node.js + Fastify + Deploy Render/Supabase

## Findings

### 1. JavaScript vs TypeScript para o novo backend

**Decision:** JavaScript (CommonJS) — arquivos `.js` conforme definido na estrutura alvo da spec.  
**Rationale:** Zero configuração de compilação; deploy mais simples no Render; codebase pequena (~500 linhas) não justifica o overhead de TS; `pg` e Fastify têm tipos JSDoc disponíveis para IDE se necessário.  
**Alternatives considered:** TypeScript — descartado por adicionar etapa de build (`tsc`) sem benefício proporcional para o escopo deste projeto.

### 2. `pg` (raw SQL) vs ORM

**Decision:** `pg` (node-postgres 8.x) com queries SQL raw.  
**Rationale:** Schema não muda; todas as queries são CRUD simples + um aggregate (grade mensal); SQL explícito é mais fácil de auditar para verificar paridade com o C# original; sem camada de codegen ou schema duplicado.  
**Alternatives considered:** Prisma, Drizzle ORM — descartados por adicionar complexidade de schema duplicado, codegen e camada de abstração desnecessária para 8 endpoints.

### 3. Fastify plugin system para injeção do pool de banco

**Decision:** `fastify.decorate('db', pool)` no plugin `db.js`, acessado em cada route como `fastify.db`.  
**Rationale:** Padrão oficial do Fastify para compartilhar recursos entre plugins; evita importação direta do módulo pg em cada arquivo de rota (Dependency Inversion); testável — rotas podem receber mock via `fastify.decorate`.  
**Alternatives considered:** Importação direta do singleton `pool` — funciona mas acopla rotas ao módulo `db.js` sem possibilidade de substituição em testes.

### 4. @fastify/static para servir o Angular build

**Decision:** Plugin `@fastify/static` apontando para `../frontend/dist/browser` com `{ root, prefix: '/' }` e `wildcard: false` — rotas `/api/*` têm prioridade; fallback para `index.html` para suportar roteamento Angular.  
**Rationale:** Fastify já está no processo — sem nginx adicional; Render free tier suporta apenas um processo por serviço; fallback para `index.html` necessário para deep links Angular funcionarem.  
**Alternatives considered:** Servir static via nginx separado — não suportado no Render free tier sem custo adicional.

### 5. ExcelJS para geração do arquivo .xlsx

**Decision:** ExcelJS 4.x — `Workbook → addWorksheet → addRow → buffer()`.  
**Rationale:** API fluente para criação de workbooks; suporte completo a estilos (fundo colorido, negrito, bordas) necessários para as abas Produção e Faltas; sem dependências nativas (bom para Render/Linux).  
**Alternatives considered:** xlsx (SheetJS community) — suporte a estilos limitado na versão gratuita; `exceljs` é o equivalente funcional do EPPlus no ecossistema Node.js.

### 6. GitHub Actions + Render Deploy Hook

**Decision:** Workflow `deploy.yml` com steps: install → test → build Angular (`ng build`) → `curl -X POST $RENDER_DEPLOY_HOOK_URL`.  
**Rationale:** Render free tier não dispara deploy automático por push — requer Deploy Hook (URL secreta configurada como GitHub Secret). GitHub Actions é gratuito para repositórios públicos/privados (2000 min/mês).  
**Alternatives considered:** Render native GitHub integration (auto-deploy por push) — disponível apenas em planos pagos com zero cold start garantido.

### 7. `schema.sql` substituindo EF Core migrations

**Decision:** Arquivo único `backend/src/db/schema.sql` com DDL completo (`CREATE TABLE IF NOT EXISTS`) — idempotente, executado manualmente no Supabase via SQL Editor na primeira configuração.  
**Rationale:** Schema não muda nesta migração; um arquivo SQL simples é mais fácil de auditar e aplicar que um sistema de migrations; Supabase tem SQL Editor no dashboard.  
**Alternatives considered:** node-pg-migrate, Flyway — descartados por adicionar complexidade de migrations sem benefício para um schema estável.

### 8. Logging com pino (built-in do Fastify)

**Decision:** Logger built-in do Fastify (pino) configurado com `{ level: process.env.LOG_LEVEL || 'info', timestamp: () => \`,"time":"\${new Date().toISOString()}"\` }`. Cada request loga automaticamente; erros de rota adicionam contexto via `request.log.error({ err, contexto })`.  
**Rationale:** Pino é structured JSON logging zero-config, já incluso no Fastify — satisfaz Princípio III da Constituição sem dependência extra; logs em JSON facilitam filtragem no Render dashboard.  
**Alternatives considered:** Winston — add 30KB de overhead; `console.error` — não estruturado, dificulta filtragem em produção.

### 9. Variáveis de ambiente

**Decision:** `dotenv` carregado em `server.js` apenas quando `NODE_ENV !== 'production'` (`require('dotenv').config()`). Variáveis: `DATABASE_URL`, `PORT` (default 3000), `LOG_LEVEL` (default `info`), `NODE_ENV`.  
**Rationale:** Padrão 12-factor app; sem hardcode de credenciais; Render injeta `DATABASE_URL` e `PORT` automaticamente em produção — sem conflito com dotenv.  
**Alternatives considered:** Arquivos de config JSON — mais frágeis que env vars para deploy em container/PaaS.

### 10. Cold start no Render free tier

**Decision:** Aceitar limitação — primeira requisição após 15 min de inatividade pode levar ~30s. Documentado na spec como "limitação conhecida aceita".  
**Rationale:** Mitigações (UptimeRobot ping a cada 14 min) são possíveis mas fora do escopo desta migração. Usuário único (gestor) foi informado e aceitou.  
**Alternatives considered:** Render paid plan (sem hibernação) — custo adicional fora do objetivo de "custo zero".
