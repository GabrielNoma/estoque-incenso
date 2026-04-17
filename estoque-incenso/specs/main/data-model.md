# Data Model: Controle de Produção Diária

## Entidades

### Funcionaria

Representa uma funcionária da empresa. Pode ser desativada sem perda de histórico.

| Campo  | Tipo         | Constraints                  | Notas                                  |
|--------|--------------|------------------------------|----------------------------------------|
| Id     | int (PK)     | identity, not null           |                                        |
| Nome   | varchar(100) | not null, unique             | Nome exibido na grade                  |
| Ativa  | bool         | not null, default true       | False = não aparece na grade diária    |

**Regras de negócio:**
- `Nome` DEVE ser único (evitar duplicatas de funcionárias com mesmo nome)
- Desativar uma funcionária NÃO apaga seus registros históricos
- Funcionária desativada NÃO aparece na grade do mês atual, mas pode ser consultada em meses passados

---

### RegistroDiario

Representa a entrada de um dia específico para uma funcionária. Uma linha por funcionária por dia.

| Campo             | Tipo          | Constraints                            | Notas                                         |
|-------------------|---------------|----------------------------------------|-----------------------------------------------|
| Id                | int (PK)      | identity, not null                     |                                               |
| FuncionariaId     | int (FK)      | not null → Funcionaria.Id              | Cascade delete: não (preservar histórico)     |
| Data              | date          | not null                               | Apenas a data, sem hora                       |
| Quantidade        | int?          | nullable, >= 0                         | Null = célula vazia (nem produção nem falta)  |
| Falta             | bool          | not null, default false                |                                               |
| MotivoFalta       | int?          | nullable, enum MotivoFalta             | Obrigatório quando Falta = true               |
| ObservacaoFalta   | varchar(500)? | nullable                               | Obrigatório quando MotivoFalta = Outro        |

**Constraint única**: `(FuncionariaId, Data)` — um registro por funcionária por dia.

**Regras de negócio:**
- `Quantidade` e `Falta = true` são mutuamente exclusivos — a célula tem um ou outro, nunca ambos
- Quando `Falta = false`, `MotivoFalta` e `ObservacaoFalta` DEVEM ser null
- Quando `MotivoFalta = Outro`, `ObservacaoFalta` é obrigatório e não pode ser vazio
- Células sem registro (nenhuma linha no banco para aquele dia) são tratadas como vazias — NÃO entram nos totais

---

### MotivoFalta (enum)

```csharp
public enum MotivoFalta
{
    Atestado = 1,
    Falta = 2,
    Outro = 3
}
```

---

## Relacionamentos

```
Funcionaria (1) ──< RegistroDiario (N)
  Funcionaria.Id = RegistroDiario.FuncionariaId
```

---

## Cálculos (lógica de negócio — sem persistir)

Todos os totais são calculados em tempo de leitura:

| Cálculo | Definição |
|---------|-----------|
| Total do dia | `SUM(Quantidade)` de todas as funcionárias ativas naquele dia |
| Total mensal por funcionária | `SUM(Quantidade)` de todos os dias do mês para a funcionária |
| Total semanal por funcionária | `SUM(Quantidade)` dos dias do mês que pertencem à semana N (segunda–sexta) |
| Faltas do mês | Contagem de `RegistroDiario` onde `Falta = true` no mês, agrupado por `MotivoFalta` |

**Regra de semana**: semana 1 = dias do mês que pertencem à primeira segunda-feira do mês (ISO week
truncado ao mês). Dias de fim de semana (sáb/dom) NÃO entram no total semanal.

---

## Schema SQL (PostgreSQL)

```sql
CREATE TABLE funcionarias (
    id      SERIAL PRIMARY KEY,
    nome    VARCHAR(100) NOT NULL,
    ativa   BOOLEAN NOT NULL DEFAULT TRUE,
    CONSTRAINT uq_funcionaria_nome UNIQUE (nome)
);

CREATE TYPE motivo_falta AS ENUM ('atestado', 'falta', 'outro');

CREATE TABLE registros_diarios (
    id                 SERIAL PRIMARY KEY,
    funcionaria_id     INT NOT NULL REFERENCES funcionarias(id),
    data               DATE NOT NULL,
    quantidade         INT CHECK (quantidade >= 0),
    falta              BOOLEAN NOT NULL DEFAULT FALSE,
    motivo_falta       motivo_falta,
    observacao_falta   VARCHAR(500),
    CONSTRAINT uq_registro_funcionaria_data UNIQUE (funcionaria_id, data),
    CONSTRAINT chk_exclusividade CHECK (
        NOT (quantidade IS NOT NULL AND falta = TRUE)
    ),
    CONSTRAINT chk_motivo_quando_falta CHECK (
        (falta = FALSE AND motivo_falta IS NULL) OR
        (falta = TRUE AND motivo_falta IS NOT NULL)
    ),
    CONSTRAINT chk_obs_quando_outro CHECK (
        motivo_falta != 'outro' OR
        (motivo_falta = 'outro' AND observacao_falta IS NOT NULL AND observacao_falta != '')
    )
);

CREATE INDEX idx_registro_data ON registros_diarios(data);
CREATE INDEX idx_registro_funcionaria ON registros_diarios(funcionaria_id);
```
