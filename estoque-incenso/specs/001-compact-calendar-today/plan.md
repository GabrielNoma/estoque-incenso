# Implementation Plan: Calendário Compacto com Data Inicial Hoje

**Branch**: `001-compact-calendar-today` | **Date**: 2026-04-23 | **Spec**: [spec.md](spec.md)
**Input**: Feature specification from `specs/001-compact-calendar-today/spec.md`

## Summary

Dois ajustes puramente visuais no frontend Angular: (1) compactar o componente `mes-selector` reduzindo larguras dos campos e eliminando o espaço de subscript reservado pelo `mat-form-field`; (2) adicionar destaque visual na coluna do dia corrente na grade de produção quando o mês carregado for o mês atual. Nenhuma mudança em backend, API ou banco de dados.

## Technical Context

**Language/Version**: TypeScript (Angular 17) + SCSS inline  
**Primary Dependencies**: Angular Material (`MatSelectModule`, `MatFormFieldModule`, `MatButtonModule`, `MatIconModule`)  
**Storage**: N/A — mudanças são exclusivamente de apresentação  
**Testing**: Angular testing utilities (se aplicável)  
**Target Platform**: Navegador web (desktop)  
**Project Type**: Web application — frontend only para esta feature  
**Performance Goals**: N/A  
**Constraints**: Sem regressões nos controles de navegação existentes  
**Scale/Scope**: 2 arquivos modificados, ~20 linhas alteradas

## Constitution Check

| Princípio | Gate | Status |
|-----------|------|--------|
| I. Simplicidade de Uso | Mudanças são CSS e um método derivado simples. Sem abstrações novas. | ✅ |
| II. Clean Code & SOLID | `eHoje(dia)` tem responsabilidade única e clara. Sem duplicação. | ✅ |
| III. Observabilidade de Erros | Mudanças puramente visuais, sem novos caminhos de erro. | ✅ |

## Project Structure

### Documentation (this feature)

```text
specs/001-compact-calendar-today/
├── plan.md              ← este arquivo
├── research.md          ← decisões de design
├── data-model.md        ← sem mudanças de modelo
├── quickstart.md        ← guia de teste manual
└── tasks.md             ← gerado por /speckit-tasks
```

### Source Code (arquivos modificados)

```text
frontend/
└── src/
    └── app/
        ├── shared/components/mes-selector/
        │   └── mes-selector.component.ts   ← compactação de estilos
        └── features/producao/grade-producao/
            └── grade-producao.component.ts ← método eHoje + classe CSS
```

## Implementation Details

### Mudança 1 — Compactação do `mes-selector`

**Arquivo**: `frontend/src/app/shared/components/mes-selector/mes-selector.component.ts`

Ajustes nos estilos inline (seção `styles`):

```scss
// ANTES
.campo-mes { width: 140px; }
.campo-ano { width: 90px; }

// DEPOIS
.mes-selector { display: flex; align-items: center; gap: 4px; }
.campo-mes { width: 110px; }
.campo-ano { width: 72px; }

// Remover espaço de subscript (faixa vazia abaixo do campo)
::ng-deep .mes-selector .mat-mdc-form-field-subscript-wrapper { display: none; }
```

O `::ng-deep` é necessário aqui para atingir o elemento interno do Angular Material. Esta é a forma padrão para customização de componentes Material sem criar um tema global.

### Mudança 2 — Destaque do dia de hoje na grade

**Arquivo**: `frontend/src/app/features/producao/grade-producao/grade-producao.component.ts`

Adicionar método na classe:
```typescript
private readonly _hoje = new Date();

eHoje(dia: number): boolean {
  const g = this.grade();
  if (!g) return false;
  return g.ano === this._hoje.getFullYear() &&
         g.mes === this._hoje.getMonth() + 1 &&
         dia === this._hoje.getDate();
}
```

No template, adicionar binding de classe na coluna do dia (cabeçalho e células):
```html
[class.dia-hoje]="eHoje(dia)"
```

Adicionar estilo (na seção `styles` do componente):
```scss
.dia-hoje { background-color: rgba(63, 81, 181, 0.12); font-weight: 600; }
```

## Complexity Tracking

> Nenhuma violação da Constituição. Tabela omitida.
