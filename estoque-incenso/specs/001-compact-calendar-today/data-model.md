# Data Model: Calendário Compacto com Data Inicial Hoje

## Mudanças de modelo

**Nenhuma mudança de modelo de dados.** Feature é exclusivamente de apresentação (UI).

## Entidades existentes afetadas (sem alteração de schema)

### `MesAno` (interface TypeScript — inalterada)

```typescript
interface MesAno {
  ano: number;  // 4-digit year
  mes: number;  // 1–12
}
```

## Lógica derivada adicionada (não persistida)

| Método/Campo | Tipo | Onde | Derivação |
|---|---|---|---|
| `eHoje(dia)` | `boolean` | `GradeProducaoComponent` | `grade.ano === hoje.getFullYear() && grade.mes === hoje.getMonth()+1 && dia === hoje.getDate()` |
| `diaSemana(dia)` | `string` | `GradeProducaoComponent` | `['Dom','Seg','Ter','Qua','Qui','Sex','Sáb'][new Date(ano, mes-1, dia).getDay()]` |
| `_hoje` | `Date` | `GradeProducaoComponent` | `new Date()` capturado uma vez na construção do componente — imutável durante a sessão |

Todos os campos são calculados no componente — sem persistência, sem chamadas de API.
