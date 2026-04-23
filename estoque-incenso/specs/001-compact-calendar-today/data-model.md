# Data Model: Calendário Compacto com Data Inicial Hoje

## Mudanças de modelo

**Nenhuma mudança de modelo de dados.** Feature é exclusivamente de apresentação (UI).

## Entidades existentes afetadas

### `MesAno` (interface TypeScript — não muda)

```typescript
interface MesAno {
  ano: number;  // 4-digit year
  mes: number;  // 1–12
}
```

### Propriedade nova (lógica derivada, não persistida)

| Propriedade | Tipo | Derivação | Uso |
|-------------|------|-----------|-----|
| `eHoje(dia)` | `boolean` | `mes === hoje.getMonth()+1 && ano === hoje.getFullYear() && dia === hoje.getDate()` | Adiciona classe CSS `dia-hoje` na coluna do dia atual |

Essa propriedade é calculada no componente `GradeProducaoComponent` — sem persistência, sem API.
