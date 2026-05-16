# Data Model: Migração para Node.js + Fastify + Deploy Render/Supabase

## Mudanças de modelo

**Nenhuma mudança no schema do banco de dados.** A migração é exclusivamente de runtime (C# → Node.js). As tabelas, constraints e índices permanecem idênticos.

## Schema PostgreSQL (inalterado)

```sql
-- Arquivo: backend/src/db/schema.sql

CREATE TABLE IF NOT EXISTS funcionarias (
  id    SERIAL PRIMARY KEY,
  nome  VARCHAR(100) NOT NULL UNIQUE,
  ativa BOOLEAN      NOT NULL DEFAULT true
);

CREATE TABLE IF NOT EXISTS registros (
  id               SERIAL  PRIMARY KEY,
  funcionaria_id   INTEGER NOT NULL REFERENCES funcionarias(id),
  ano              INTEGER NOT NULL,
  mes              INTEGER NOT NULL CHECK (mes BETWEEN 1 AND 12),
  dia              INTEGER NOT NULL CHECK (dia BETWEEN 1 AND 31),
  quantidade       INTEGER          CHECK (quantidade >= 0),
  falta            BOOLEAN NOT NULL DEFAULT false,
  motivo_falta     VARCHAR(20)      CHECK (motivo_falta IN ('atestado', 'falta', 'outro')),
  observacao_falta TEXT,
  UNIQUE (funcionaria_id, ano, mes, dia)
);
```

## Entidades e mapeamento JSON ↔ SQL

### Funcionária

| JSON (API)  | SQL (coluna)  | Tipo           | Notas                         |
|-------------|---------------|----------------|-------------------------------|
| `id`        | `id`          | SERIAL / int   | PK, gerado pelo banco          |
| `nome`      | `nome`        | VARCHAR(100)   | UNIQUE; validado na rota      |
| `ativa`     | `ativa`       | BOOLEAN        | Default true no INSERT        |

### Registro

| JSON (API)        | SQL (coluna)      | Tipo         | Notas                                     |
|-------------------|-------------------|--------------|-------------------------------------------|
| `id`              | `id`              | SERIAL / int | PK                                        |
| `funcionariaId`   | `funcionaria_id`  | INTEGER      | FK → funcionarias.id                      |
| `data`            | `ano`, `mes`, `dia` | INTEGER×3  | `"2026-04-03"` → `{ano:2026, mes:4, dia:3}` |
| `quantidade`      | `quantidade`      | INTEGER      | NULL se falta; ≥ 0                        |
| `falta`           | `falta`           | BOOLEAN      | Default false                             |
| `motivoFalta`     | `motivo_falta`    | VARCHAR(20)  | NULL se não é falta                       |
| `observacaoFalta` | `observacao_falta`| TEXT         | Obrigatório se motivo = 'outro'           |

## Regras de validação (camada de rota — não no banco)

| Regra | Código HTTP | Mensagem |
|-------|-------------|----------|
| `quantidade` preenchido + `falta: true` | 400 | `"Quantidade e falta não podem ser informados simultaneamente."` |
| `falta: true` + `motivoFalta` ausente | 400 | `"Motivo de falta é obrigatório."` |
| `motivoFalta: 'outro'` + `observacaoFalta` vazia | 400 | `"Observação é obrigatória para motivo 'Outro'."` |
| `quantidade < 0` | 400 | `"Quantidade deve ser maior ou igual a zero."` |
| Nome de funcionária duplicado | 409 | `"Funcionária com este nome já existe."` |
| Funcionária não encontrada | 404 | — |
| Registro não encontrado | 404 | — |

## Conversão de data

A API usa `"data": "YYYY-MM-DD"` (ISO 8601). O banco armazena `ano`, `mes`, `dia` como inteiros separados.

```javascript
// JSON → SQL
const [ano, mes, dia] = req.body.data.split('-').map(Number)

// SQL → JSON (na query GET /api/registros)
data: `${r.ano}-${String(r.mes).padStart(2,'0')}-${String(r.dia).padStart(2,'0')}`
```
