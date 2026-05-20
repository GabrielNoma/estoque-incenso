# Implementation Plan: Calendário Compacto com Data Inicial Hoje

**Branch**: `001-compact-calendar-today` | **Date**: 2026-05-13 | **Spec**: [spec.md](./spec.md)  
**Input**: Feature specification from `/specs/001-compact-calendar-today/spec.md`

## Summary

Duas mudanças puramente visuais/comportamentais no frontend Angular: (1) compactar o `MesSelectorComponent` reduzindo widths, gaps, altura e adicionando bordas pill; (2) inicializar `GradeProducaoComponent` no mês/dia correntes e rolar automaticamente até o dia de hoje com destaque laranja na coluna.

## Technical Context

**Language/Version**: TypeScript 5.x (Angular 17, standalone components)  
**Primary Dependencies**: Angular Material MDC (`MatSelectModule`, `MatFormFieldModule`, `MatButtonModule`, `MatIconModule`), `CommonModule`, `FormsModule`  
**Storage**: N/A — mudanças são exclusivamente de apresentação  
**Testing**: `npm test` (Angular testing utilities)  
**Target Platform**: Browser (SPA Angular servida pelo .NET backend)  
**Project Type**: Web application — frontend SPA  
**Performance Goals**: Scroll to today imperceptível ao usuário (~1 rAF)  
**Constraints**: Sem alterações de API; nenhum novo módulo Angular; compatível com Angular 17 standalone  
**Scale/Scope**: 2 arquivos modificados, 0 arquivos novos

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Princípio | Gate | Status |
|-----------|------|--------|
| I. Simplicidade de Uso | `eHoje()`, `diaSemana()`, classes CSS com nomes claros; nenhuma abstração desnecessária | ✅ |
| II. Clean Code & SOLID | Lógica de "hoje" encapsulada em `eHoje()`; patch otimista em métodos privados dedicados; SRP mantido | ✅ |
| III. Observabilidade de Erros | Operações de UI pura; erros de rede delegados ao `carregar()` existente com `error:` handler; nenhum catch vazio | ✅ |

*Nenhuma violação. Complexity Tracking não necessário.*

## Project Structure

### Documentation (this feature)

```text
specs/001-compact-calendar-today/
├── plan.md              # Este arquivo
├── research.md          # Phase 0 — decisões de estilo e inicialização
├── data-model.md        # N/A (sem mudanças de domínio)
├── quickstart.md        # Como executar e verificar
└── tasks.md             # Phase 2 output (/speckit-tasks)
```

### Source Code (arquivos afetados)

```text
frontend/
└── src/app/
    ├── shared/components/mes-selector/
    │   └── mes-selector.component.ts   ← compactação visual
    └── features/producao/grade-producao/
        └── grade-producao.component.ts ← inicialização hoje + highlight + scroll
```

**Structure Decision**: Dois componentes existentes modificados. Nenhum arquivo novo criado. Opção de extrair `eHoje()` para utilitário foi rejeitada (YAGNI — uso único).
