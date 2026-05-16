# Implementation Plan: Migração para Node.js + Fastify + Deploy Render/Supabase

**Branch**: `002-migrate-node-fastify` | **Date**: 2026-05-13 | **Spec**: [spec.md](./spec.md)  
**Input**: Feature specification from `/specs/002-migrate-node-fastify/spec.md`

## Summary

Migração completa do backend de C# .NET 8 para Node.js 20 LTS + Fastify 5, mantendo os 8 endpoints com mesmos paths e payloads, servindo o build Angular como arquivos estáticos, com deploy automatizado via GitHub Actions no Render e banco PostgreSQL no Supabase.

## Technical Context

**Language/Version**: Node.js 20 LTS + JavaScript (CommonJS)  
**Primary Dependencies**: Fastify 5, pg (node-postgres 8.x), ExcelJS 4.x, @fastify/cors, @fastify/static, dotenv  
**Storage**: PostgreSQL 16 via `pg` pool com queries SQL raw; Supabase free tier em produção  
**Testing**: `node:test` (built-in) — smoke tests mínimos de rotas; sem suite existente no projeto  
**Target Platform**: Linux (Render Web Service free tier); desenvolvimento local Windows/macOS  
**Project Type**: Web service (REST API + servidor de arquivos estáticos Angular)  
**Performance Goals**: Cold start ~30s (limitação conhecida do Render free tier); p95 < 200ms em operação normal  
**Constraints**: Render free tier (hibernação após 15 min); Supabase 500MB; sem autenticação; 1 serviço único (API + static)  
**Scale/Scope**: 1 usuário, 8 endpoints, 3 domínios de rotas, ~500 linhas de código total

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Princípio | Gate | Status |
|-----------|------|--------|
| I. Simplicidade de Uso | Routes nomeadas por domínio; SQL raw sem ORM; Fastify plugins injetam dependências sem acoplamento; sem abstrações antecipadas (YAGNI) | ✅ |
| II. Clean Code & SOLID | Cada arquivo de rota tem responsabilidade única (SRP); `db.js` centraliza pool (DI); `app.js` apenas compõe plugins e rotas; `server.js` apenas faz listen | ✅ |
| III. Observabilidade de Erros | Fastify inclui pino (structured JSON logs); configurado com timestamps ISO e nível via `LOG_LEVEL`; error handlers explícitos; catch vazio proibido | ✅ |

*Nenhuma violação. Complexity Tracking não necessário.*

## Project Structure

### Documentation (this feature)

```text
specs/002-migrate-node-fastify/
├── plan.md              # Este arquivo
├── research.md          # Phase 0 — decisões de arquitetura e tecnologia
├── data-model.md        # Schema SQL + mapeamento JSON→SQL
├── quickstart.md        # Como executar e verificar endpoints
├── contracts/
│   ├── funcionarias.md  # Contrato GET/POST/PUT/PATCH funcionárias
│   ├── registros.md     # Contrato GET/PUT/DELETE registros
│   └── exportacao.md    # Contrato GET /excel
└── tasks.md             # Phase 2 output (/speckit-tasks — não criado aqui)
```

### Source Code (arquivos criados/modificados)

```text
backend/                          ← substitui o backend C# inteiro
  src/
    routes/
      funcionarias.js             ← GET/POST/PUT/PATCH
      registros.js                ← GET/PUT/DELETE
      exportacao.js               ← GET /excel
    plugins/
      db.js                       ← pool pg via fastify.decorate('db', pool)
      cors.js                     ← @fastify/cors
      static.js                   ← @fastify/static → ../frontend/dist/browser
    db/
      schema.sql                  ← DDL completo (substitui EF Core migrations)
  app.js                          ← instância Fastify + plugins + rotas
  server.js                       ← entrypoint: app.listen(PORT)
  .env.example                    ← DATABASE_URL, PORT, LOG_LEVEL
  package.json

.github/
  workflows/
    deploy.yml                    ← build Angular → curl Deploy Hook do Render
```

**Structure Decision**: Backend Node.js substitui `backend/` inteiro. Frontend Angular mantido sem nenhuma alteração. CI/CD via GitHub Actions + Deploy Hook (não native Render GitHub integration, que requer plano pago).
