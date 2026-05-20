# estoque-incenso Development Guidelines

Auto-generated from all feature plans. Last updated: 2026-05-13

## Active Technologies
- TypeScript (Angular 17) + SCSS inline + Angular Material (`MatSelectModule`, `MatFormFieldModule`, `MatButtonModule`, `MatIconModule`) (001-compact-calendar-today)
- N/A — mudanças são exclusivamente de apresentação (001-compact-calendar-today)
- TypeScript 5.x (Angular 17, standalone components) + Angular Material MDC (`MatSelectModule`, `MatFormFieldModule`, `MatButtonModule`, `MatIconModule`), `CommonModule`, `FormsModule` (001-compact-calendar-today)
- Node.js 20 LTS + JavaScript (CommonJS) + Fastify 5, pg (node-postgres 8.x), ExcelJS 4.x, @fastify/cors, @fastify/static, dotenv (002-migrate-node-fastify)
- PostgreSQL 16 via `pg` pool com queries SQL raw; Supabase free tier em produção (002-migrate-node-fastify)

- C# (.NET 8), TypeScript (Angular 17) + Angular 17, Angular Material, .NET 8 Web API, Entity Framework Core 8, EPPlus 7, PostgreSQL 16, Npgsql (main)

## Project Structure

```text
backend/
frontend/
tests/
```

## Commands

npm test; npm run lint

## Code Style

C# (.NET 8), TypeScript (Angular 17): Follow standard conventions

## Recent Changes
- 002-migrate-node-fastify: Added Node.js 20 LTS + JavaScript (CommonJS) + Fastify 5, pg (node-postgres 8.x), ExcelJS 4.x, @fastify/cors, @fastify/static, dotenv
- 001-compact-calendar-today: Added TypeScript 5.x (Angular 17, standalone components) + Angular Material MDC (`MatSelectModule`, `MatFormFieldModule`, `MatButtonModule`, `MatIconModule`), `CommonModule`, `FormsModule`
- 001-compact-calendar-today: Added TypeScript (Angular 17) + SCSS inline + Angular Material (`MatSelectModule`, `MatFormFieldModule`, `MatButtonModule`, `MatIconModule`)


<!-- MANUAL ADDITIONS START -->
<!-- MANUAL ADDITIONS END -->
