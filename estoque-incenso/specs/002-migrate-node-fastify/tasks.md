# Tasks: Migração para Node.js + Fastify + Deploy Render/Supabase

**Input**: Design documents from `/specs/002-migrate-node-fastify/`
**Prerequisites**: plan.md ✅, spec.md ✅, research.md ✅, data-model.md ✅, contracts/ ✅, quickstart.md ✅
**Branch**: `002-migrate-node-fastify`

**Tests**: Não solicitados explicitamente — sem tarefas de teste automatizado. Validação via cenários manuais do quickstart.md.

**Organization**: Tarefas agrupadas por user story para implementação e teste independentes.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Pode rodar em paralelo (arquivos diferentes, sem dependências incompletas)
- **[Story]**: User story correspondente (US1–US4)

---

## Phase 1: Setup

**Purpose**: Inicialização do projeto Node.js e estrutura de diretórios

- [ ] T001 Create backend directory structure: `backend/src/routes/`, `backend/src/plugins/`, `backend/src/db/` per plan.md
- [ ] T002 Create `backend/package.json` with `"engines": { "node": ">=20" }`, Fastify 5, pg 8.x, ExcelJS 4.x, @fastify/cors, @fastify/static, dotenv as dependencies; `"main": "server.js"`; `"start": "node server.js"` script
- [ ] T003 [P] Create `backend/.env.example` with DATABASE_URL=postgresql://user:pass@host:5432/dbname, PORT=3000, LOG_LEVEL=info, NODE_ENV=development

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Infraestrutura central que DEVE ser concluída antes de qualquer user story

**⚠️ CRÍTICO**: Nenhum trabalho de user story pode começar antes desta fase

- [ ] T004 Create `backend/src/db/schema.sql` with DDL completo: `CREATE TABLE IF NOT EXISTS funcionarias (id SERIAL PRIMARY KEY, nome VARCHAR(100) NOT NULL UNIQUE, ativa BOOLEAN NOT NULL DEFAULT true)` e `CREATE TABLE IF NOT EXISTS registros` com todas as colunas, constraints e `UNIQUE (funcionaria_id, ano, mes, dia)` conforme data-model.md
- [ ] T005 Create `backend/src/plugins/db.js` as Fastify plugin: cria `pg.Pool({ connectionString: process.env.DATABASE_URL })`, registra via `fastify.decorate('db', pool)`, fecha pool no hook `onClose`
- [ ] T006 [P] Create `backend/src/plugins/cors.js` as Fastify plugin registering `@fastify/cors` with `{ origin: true }` (permite todas as origens; restringir em produção se necessário)
- [ ] T007 [P] Create `backend/src/plugins/static.js` as Fastify plugin registering `@fastify/static` with `{ root: path.join(__dirname, '../../frontend/dist/browser'), prefix: '/', wildcard: false }`; adiciona hook `onRequest` para servir `index.html` em rotas não-API (fallback para roteamento Angular)
- [ ] T008 Create `backend/app.js`: cria instância Fastify com `{ logger: { level: process.env.LOG_LEVEL || 'info', timestamp: () => \`,"time":"\${new Date().toISOString()}"\` } }`; registra plugins db, cors e static via `fastify.register()`; registra rotas `funcionarias`, `registros` e `exportacao` com prefixo `/api`; exporta `app` (não faz listen)
- [ ] T009 Create `backend/server.js`: carrega `require('dotenv').config()` apenas quando `process.env.NODE_ENV !== 'production'`; importa `app` de `./app.js`; chama `app.listen({ port: Number(process.env.PORT) || 3000, host: '0.0.0.0' })`; loga URL em sucesso; encerra processo em erro

**Checkpoint**: `node backend/server.js` inicia sem erros; `GET http://localhost:3000/api/funcionarias` retorna 404 (route files ainda não criados)

---

## Phase 3: User Story 1 — Cadastro de Funcionárias (Priority: P1) 🎯 MVP

**Goal**: Listar, criar, editar nome e ativar/desativar funcionárias via API REST

**Independent Test**:
- `GET /api/funcionarias` → array JSON com funcionárias ativas
- `GET /api/funcionarias?includeInactive=true` → inclui inativas
- `POST /api/funcionarias { "nome": "Ana" }` → 201 com `{ id, nome, ativa: true }`
- `POST /api/funcionarias { "nome": "Ana" }` (duplicado) → 409 `{ "error": "Funcionária com este nome já existe." }`
- `PUT /api/funcionarias/1 { "nome": "Ana Silva" }` → 200 com registro atualizado
- `PUT /api/funcionarias/999` → 404
- `PATCH /api/funcionarias/1/status { "ativa": false }` → 200 com `ativa: false`
- `PATCH /api/funcionarias/999/status` → 404

### Implementation

- [ ] T010 [US1] Create `backend/src/routes/funcionarias.js` exporting async Fastify plugin; implement `GET /api/funcionarias`: `SELECT id, nome, ativa FROM funcionarias` com `WHERE ativa = true` quando `request.query.includeInactive` não é `'true'`; responde array JSON
- [ ] T011 [US1] Add `POST /api/funcionarias` to `backend/src/routes/funcionarias.js`: valida `body.nome` não vazio; `INSERT INTO funcionarias (nome) VALUES ($1) RETURNING *`; captura erro PostgreSQL código `'23505'` (violação UNIQUE) e responde 409 `{ "error": "Funcionária com este nome já existe." }`; responde 201 com objeto inserido
- [ ] T012 [US1] Add `PUT /api/funcionarias/:id` to `backend/src/routes/funcionarias.js`: `UPDATE funcionarias SET nome=$1 WHERE id=$2 RETURNING *`; se `result.rowCount === 0` responde 404; retorna 200 com registro atualizado
- [ ] T013 [US1] Add `PATCH /api/funcionarias/:id/status` to `backend/src/routes/funcionarias.js`: `UPDATE funcionarias SET ativa=$1 WHERE id=$2 RETURNING *`; se `result.rowCount === 0` responde 404; retorna 200 com registro atualizado

**Checkpoint**: Todos os 4 endpoints respondem conforme contrato em `specs/002-migrate-node-fastify/contracts/funcionarias.md`

---

## Phase 4: User Story 2 — Grade de Produção + Faltas (Priority: P2)

**Goal**: Carregar grade mensal, salvar e excluir registros diários (produção ou falta)

**Independent Test**:
- `GET /api/registros?ano=2026&mes=5` → `{ ano: 2026, mes: 5, funcionarias: [{ id, nome, ativa, registros: [{ id, data, quantidade, falta, motivoFalta, observacaoFalta }] }] }`
- `PUT /api/registros { "funcionariaId":1, "data":"2026-05-13", "quantidade":50, "falta":false }` → 200
- `PUT /api/registros { "funcionariaId":1, "data":"2026-05-13", "quantidade":50, "falta":true }` → 400 (simultâneo)
- `PUT /api/registros { "funcionariaId":1, "data":"2026-05-13", "falta":true }` (sem motivo) → 400
- `PUT /api/registros { "funcionariaId":999, ... }` → 404
- `DELETE /api/registros/1` → 204
- `DELETE /api/registros/999` → 404

### Implementation

- [ ] T014 [US2] Create `backend/src/routes/registros.js` exporting async Fastify plugin; implement `GET /api/registros`: valida query params `ano` e `mes` (inteiros, obrigatórios); executa JOIN `funcionarias LEFT JOIN registros ON ...` filtrando por ano e mes (inclui funcionárias ativas + inativas com registro no mês); agrupa registros por funcionária em JS; converte colunas snake_case → camelCase (`funcionaria_id` → `funcionariaId`, `motivo_falta` → `motivoFalta`, `observacao_falta` → `observacaoFalta`) e `(ano, mes, dia)` → `"YYYY-MM-DD"` na field `data`; responde `{ ano, mes, funcionarias: [...] }`
- [ ] T015 [US2] Add `PUT /api/registros` to `backend/src/routes/registros.js`: aplica todas as validações do data-model.md em ordem — quantidade + falta simultâneos → 400 `"Quantidade e falta não podem ser informados simultaneamente."`; falta sem motivoFalta → 400 `"Motivo de falta é obrigatório."`; motivoFalta 'outro' sem observacaoFalta → 400 `"Observação é obrigatória para motivo 'Outro'."` ; quantidade < 0 → 400; converte `data` ISO → `(ano, mes, dia)`; verifica funcionária existe (404); executa `INSERT INTO registros ... ON CONFLICT (funcionaria_id, ano, mes, dia) DO UPDATE SET ... RETURNING *`; retorna 200 com registro em camelCase
- [ ] T016 [US2] Add `DELETE /api/registros/:id` to `backend/src/routes/registros.js`: `DELETE FROM registros WHERE id=$1`; se `result.rowCount === 0` responde 404; responde 204 sem body

**Checkpoint**: Grade de produção do frontend Angular carrega, salva e exclui registros corretamente via novo backend Fastify

---

## Phase 5: User Story 3 — Exportação Excel (Priority: P3)

**Goal**: Gerar e baixar arquivo `.xlsx` com aba Produção e aba Faltas

**Independent Test**:
- `GET /api/exportacao/excel?ano=2026&mes=5` → download `producao_2026_05.xlsx`
- Arquivo tem 2 abas: "Produção" e "Faltas"
- Aba Produção: colunas Funcionária + dias 1–N + colunas "Sem X" (totais semanais ISO intercalados) + coluna "Total"
- Células de falta: texto "FALTA" com fundo amarelo
- Fins de semana: fundo cinza claro
- Colunas semanais ISO: fundo azul claro
- Linha de total do dia: negrito, fundo cinza
- Aba Faltas: colunas Funcionária, Data, Motivo, Observação
- `GET /api/exportacao/excel` (sem params) → 400

### Implementation

- [ ] T017 [US3] Create `backend/src/routes/exportacao.js` exporting async Fastify plugin; implement `GET /api/exportacao/excel`: valida `ano` e `mes` obrigatórios e inteiros válidos (400 se inválidos); executa a mesma query de registros de US2 (JOIN funcionarias + registros por ano e mes); usa ExcelJS — cria `new ExcelJS.Workbook()`; aba **"Produção"**: linha de cabeçalho com "Funcionária" + dias 1–N do mês com colunas "Sem X" intercaladas após último dia de cada semana ISO + "Total"; para cada funcionária, preenche quantidade ou "FALTA" por dia; aplica estilos (fundo amarelo em falta `FFFF00`, cinza claro em fim de semana `D3D3D3`, azul claro em semana ISO `BDD7EE`, negrito em totais e linha de total do dia, fundo cinza na linha de total `C0C0C0`); adiciona linha "TOTAL DIA" ao final; aba **"Faltas"**: cabeçalho [Funcionária, Data, Motivo, Observação] + rows de registros com `falta=true`; gera buffer com `workbook.xlsx.writeBuffer()`; define headers `Content-Type: application/vnd.openxmlformats-officedocument.spreadsheetml.sheet` e `Content-Disposition: attachment; filename="producao_YYYY_MM.xlsx"`; responde com buffer

**Checkpoint**: Download do Excel gera arquivo com estrutura e estilos equivalentes ao comportamento atual do backend C#

---

## Phase 6: User Story 4 — CI/CD + Deploy (Priority: P4)

**Goal**: Push para `main` aciona pipeline que faz build do Angular e deploy automático no Render

**Independent Test**:
- Arquivo `.github/workflows/deploy.yml` é YAML válido
- Push para `main` → GitHub Actions executa todos os steps sem falha
- Render recebe Deploy Hook e a aplicação é atualizada

### Implementation

- [ ] T018 [US4] Create `.github/workflows/deploy.yml`: trigger `on: push: branches: [main]`; job `build-and-deploy` rodando em `ubuntu-latest`; steps: (1) `actions/checkout@v4`; (2) `actions/setup-node@v4` com `node-version: '20'`; (3) `npm ci` no diretório `backend/`; (4) `npm ci` no diretório `frontend/`; (5) `npm run build` no diretório `frontend/` (gera `frontend/dist/browser`); (6) `curl -s -o /dev/null -w "%{http_code}" -X POST "${{ secrets.RENDER_DEPLOY_HOOK_URL }}"` e valida status 201; adiciona comentário no YAML documentando que `RENDER_DEPLOY_HOOK_URL` deve ser configurado em GitHub Settings → Secrets

**Checkpoint**: `deploy.yml` aprovado por GitHub Actions syntax check; segredo necessário documentado

---

## Phase 7: Polish & Verificação Final

**Purpose**: Validação cruzada e verificação de todos os critérios de aceite do spec

- [ ] T019 [P] Verify all 8 API endpoints in `backend/src/routes/` against contracts in `specs/002-migrate-node-fastify/contracts/` — confirma paths, métodos HTTP, query params, formatos de response (camelCase), HTTP status codes e mensagens de erro estão corretos
- [ ] T020 [P] Verify `backend/app.js` registers all 3 route files (funcionarias, registros, exportacao) and all 3 plugins (db, cors, static) with Fastify plugin encapsulation; verifica que rotas `/api/*` têm prioridade sobre static file serving
- [ ] T021 Run quickstart.md validation: execute os 8 cenários de verificação manual, confirme todos os 7 critérios de aceite do spec (endpoints, grade, Excel, frontend Angular sem alterações, GitHub Actions, Render, Supabase)

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: Sem dependências — pode iniciar imediatamente
- **Foundational (Phase 2)**: Depende de Phase 1 — **BLOQUEIA todas as user stories**
- **US1 (Phase 3)**: Depende de Phase 2 — independente de US2 e US3
- **US2 (Phase 4)**: Depende de Phase 2 — independente de US1
- **US3 (Phase 5)**: Depende de Phase 2 — independente; pode aproveitar lógica de query similar à US2
- **US4 (Phase 6)**: Depende logicamente de US1 + US2 + US3 (deploy com tudo funcional)
- **Polish (Phase 7)**: Depende de todas as user stories concluídas

### User Story Dependencies

- **US1 (P1)**: Pode iniciar após Phase 2 — sem dependência de outras stories
- **US2 (P2)**: Pode iniciar após Phase 2 — sem dependência de US1
- **US3 (P3)**: Pode iniciar após Phase 2 — sem dependência de US1/US2 (apenas usa `fastify.db` do plugin)
- **US4 (P4)**: Inicia após US1+US2+US3 para garantir deploy com backend completo

### Within Each User Story

- Rotas criadas sequencialmente no mesmo arquivo (base plugin → GET → POST/PUT/DELETE)
- Plugins T006 [P] e T007 [P] podem ser criados em paralelo com T005
- T008 (`app.js`) depende de T005, T006, T007 (precisa importar todos os plugins)
- T009 (`server.js`) depende de T008

### Parallel Opportunities

- T003 pode ser criado em paralelo com T002 (arquivos diferentes)
- T006 e T007 podem ser criados em paralelo entre si (após T001)
- US1, US2 e US3 podem ser distribuídas a agentes diferentes após Phase 2
- T019 e T020 na fase Polish podem rodar em paralelo

---

## Parallel Example: Multi-Agent

```bash
# Após Phase 2 completa (T001–T009 concluídos):

# Agente A → US1 (funcionarias.js)
Task T010: "Create backend/src/routes/funcionarias.js with GET /api/funcionarias"
Task T011: "Add POST /api/funcionarias"
Task T012: "Add PUT /api/funcionarias/:id"
Task T013: "Add PATCH /api/funcionarias/:id/status"

# Agente B → US2 + US3 (registros.js + exportacao.js) em paralelo com Agente A
Task T014: "Create backend/src/routes/registros.js with GET /api/registros"
Task T015: "Add PUT /api/registros with validation"
Task T016: "Add DELETE /api/registros/:id"
Task T017: "Create backend/src/routes/exportacao.js with GET /api/exportacao/excel"

# Após ambos concluídos:
Task T018: "Create .github/workflows/deploy.yml"
Tasks T019–T021: Polish & verificação final
```

---

## Implementation Strategy

### MVP (User Story 1 apenas)

1. Phase 1: Setup
2. Phase 2: Foundational (CRÍTICO — bloqueia tudo)
3. Phase 3: US1 — Cadastro de funcionárias
4. **PARAR E VALIDAR**: todos os 4 endpoints de funcionárias funcionam conforme contrato
5. Deploy/demo se aprovado

### Entrega Incremental

1. Setup + Foundational → infraestrutura pronta
2. US1 → funcionárias funcionando → validar
3. US2 → grade + faltas funcionando → validar
4. US3 → exportação Excel → validar
5. US4 → CI/CD ativo → deploy em produção
6. Polish → verificação final de todos os critérios de aceite

---

## Notes

- [P] = arquivos diferentes, sem dependências incompletas — podem rodar em agentes paralelos
- [Story] mapeia cada tarefa à user story para rastreabilidade
- Frontend Angular: **zero alterações de código** — nenhuma tarefa de frontend neste spec
- Cada user story é independentemente implementável e testável via quickstart.md
- Sem autenticação: sistema de uso interno/local
- Validar via cenários manuais do quickstart.md após cada story
- Fazer commit após cada fase ou grupo lógico de tarefas
