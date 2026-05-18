# Data Model: Migração para Node.js + Fastify + Deploy Render/Supabase

## Mudanças de modelo

A migração é exclusivamente de runtime (C# → Node.js). As tabelas e índices permanecem os mesmos criados pelo EF Core, com uma diferença de nomenclatura: a tabela de registros usa `registros_diarios` com coluna `data DATE` (em vez de `registros` com `ano/mes/dia` inteiros previstos inicialmente). O `schema.sql` reflete o banco real.

## Schema PostgreSQL (banco existente + script para Supabase)

```sql
-- Arquivo: backend/src/db/schema.sql

CREATE TABLE IF NOT EXISTS funcionarias (
  id    SERIAL PRIMARY KEY,
  nome  VARCHAR(100) NOT NULL,
  ativa BOOLEAN      NOT NULL DEFAULT true,
  CONSTRAINT uq_funcionaria_nome UNIQUE (nome)
);

CREATE TABLE IF NOT EXISTS registros_diarios (
  id               SERIAL  PRIMARY KEY,
  funcionaria_id   INTEGER NOT NULL REFERENCES funcionarias(id) ON DELETE RESTRICT,
  data             DATE    NOT NULL,
  quantidade       INTEGER,
  falta            BOOLEAN NOT NULL DEFAULT false,
  motivo_falta     TEXT,
  observacao_falta VARCHAR(500),
  CONSTRAINT uq_registro_funcionaria_data  UNIQUE (funcionaria_id, data),
  CONSTRAINT chk_quantidade_positiva       CHECK ((quantidade >= 0) OR (quantidade IS NULL)),
  CONSTRAINT chk_exclusividade             CHECK (NOT ((quantidade IS NOT NULL) AND (falta = true))),
  CONSTRAINT chk_motivo_quando_falta       CHECK (((falta = false) AND (motivo_falta IS NULL)) OR ((falta = true) AND (motivo_falta IS NOT NULL))),
  CONSTRAINT chk_obs_quando_outro          CHECK ((motivo_falta <> 'outro') OR ((motivo_falta = 'outro') AND (observacao_falta IS NOT NULL) AND (observacao_falta <> '')))
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
| `data`            | `data`            | DATE         | `"2026-04-03"` → `TO_CHAR(data, 'YYYY-MM-DD')` |
| `quantidade`      | `quantidade`      | INTEGER      | NULL se falta; ≥ 0                        |
| `falta`           | `falta`           | BOOLEAN      | Default false                             |
| `motivoFalta`     | `motivo_falta`    | TEXT         | NULL se não é falta; valores: `'atestado'`, `'falta'`, `'outro'` |
| `observacaoFalta` | `observacao_falta`| VARCHAR(500) | Obrigatório se motivo = 'outro'           |

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

A API usa `"data": "YYYY-MM-DD"` (ISO 8601). O banco armazena como coluna `DATE`.

```javascript
// JSON → SQL: passa a string ISO diretamente; PostgreSQL converte automaticamente
await db.query('INSERT INTO registros_diarios (..., data, ...) VALUES (..., $1, ...)', [body.data])

// SQL → JSON: usa TO_CHAR na query
TO_CHAR(r.data, 'YYYY-MM-DD') AS data_iso
```
