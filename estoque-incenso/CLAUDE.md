# estoque-incenso Development Guidelines

Auto-generated from all feature plans. Last updated: 2026-05-13

## Active Technologies
- TypeScript (Angular 17) + SCSS inline + Angular Material (`MatSelectModule`, `MatFormFieldModule`, `MatButtonModule`, `MatIconModule`) (001-compact-calendar-today)
- N/A — mudanças são exclusivamente de apresentação (001-compact-calendar-today)
- TypeScript 5.x (Angular 17, standalone components) + Angular Material MDC (`MatSelectModule`, `MatFormFieldModule`, `MatButtonModule`, `MatIconModule`), `CommonModule`, `FormsModule` (001-compact-calendar-today)
- Node.js 20 LTS + JavaScript (CommonJS) + Fastify 5, pg (node-postgres 8.x), ExcelJS 4.x, @fastify/cors, @fastify/static, dotenv (002-migrate-node-fastify)
- PostgreSQL 16 via `pg` pool com queries SQL raw; Supabase free tier em produção (002-migrate-node-fastify)

## Project Structure

```text
backend/
frontend/
tests/
```

## Commands

npm test; npm run lint

## Code Style

JavaScript (Node.js 20, CommonJS) no backend e TypeScript (Angular 17) no frontend: Follow standard conventions

## Recent Changes
- testes do backend só rodam contra Postgres local: `tests/guardaBancoDeTeste.js` bloqueia `NODE_ENV=production` e host remoto no `DATABASE_URL`
- inativa fora da grade, dentro do resumo/Excel: funcionária inativa nunca aparece no calendário (filtro `ativa` no frontend), mas entra em totais, Resumo Mensal e Excel dos meses em que tem registros. Regra única em `backend/src/queries/producaoMensal.js` (usada por `/registros` e `/exportacao/excel`). `inativada_em` continua gravada no `PATCH /status` (data ao inativar, NULL ao reativar) apenas como histórico: nenhuma consulta a lê e a API não a devolve; `ativa` é a exclusão lógica pois `registros_diarios` referencia `funcionarias` (ON DELETE RESTRICT)
- fix interceptor HTTP: lia `error.erro`, mas o backend responde `{ error }`
- 002-migrate-node-fastify: Added Node.js 20 LTS + JavaScript (CommonJS) + Fastify 5, pg (node-postgres 8.x), ExcelJS 4.x, @fastify/cors, @fastify/static, dotenv
- 001-compact-calendar-today: Added TypeScript 5.x (Angular 17, standalone components) + Angular Material MDC (`MatSelectModule`, `MatFormFieldModule`, `MatButtonModule`, `MatIconModule`), `CommonModule`, `FormsModule`
- 001-compact-calendar-today: Added TypeScript (Angular 17) + SCSS inline + Angular Material (`MatSelectModule`, `MatFormFieldModule`, `MatButtonModule`, `MatIconModule`)


<!-- MANUAL ADDITIONS START -->
<!-- MANUAL ADDITIONS END -->
