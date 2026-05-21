# Tasks: Calendário Compacto com Data Inicial Hoje

**Input**: Design documents from `specs/001-compact-calendar-today/`  
**Prerequisites**: plan.md ✅ spec.md ✅ research.md ✅ data-model.md ✅ quickstart.md ✅

**Escopo**: 2 arquivos frontend modificados. Sem backend, sem API, sem banco.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Pode rodar em paralelo (arquivos diferentes, sem dependências)
- **[Story]**: História de usuário à qual a tarefa pertence (US1/US2)
- Paths relativos à raiz do repositório

---

## Phase 1: Setup

**Purpose**: Confirmar ambiente de desenvolvimento funcional

- [x] T001 Iniciar o servidor Angular (`ng serve` em `frontend/`) e confirmar que a aplicação carrega sem erros em `localhost:4200`

**Checkpoint**: App rodando em `localhost:4200`

---

## Phase 2: US1 — Compactação do mes-selector (RF03, RF04)

**Goal**: O seletor de mês/ano ocupa menos espaço vertical e horizontal, mantendo todos os controles funcionais.

**Independent Test**: Abrir o sistema e verificar visualmente que o seletor de mês/ano é menor que o anterior; navegar entre meses para confirmar que os botões e dropdowns continuam funcionando.

- [x] T002 [US1] Reduzir `gap` do `.mes-selector` de 8px → 2px em `frontend/src/app/shared/components/mes-selector/mes-selector.component.ts`
- [x] T003 [US1] Reduzir largura de `campo-mes` de 140px → 118px e `campo-ano` de 90px → 86px em `frontend/src/app/shared/components/mes-selector/mes-selector.component.ts`
- [x] T004 [US1] Adicionar `::ng-deep .campo-mes .mat-mdc-form-field-subscript-wrapper, ::ng-deep .campo-ano .mat-mdc-form-field-subscript-wrapper { display: none; }` em `frontend/src/app/shared/components/mes-selector/mes-selector.component.ts`
- [x] T005 [US1] Definir altura fixa de 34px no `.mat-mdc-form-field-flex` via `::ng-deep` em `frontend/src/app/shared/components/mes-selector/mes-selector.component.ts`
- [x] T006 [US1] Aplicar bordas pill (border-radius 17px) via `::ng-deep` nas partes leading/trailing do `mdc-notched-outline` em `frontend/src/app/shared/components/mes-selector/mes-selector.component.ts`
- [x] T007 [US1] Reduzir espessura da borda para 1.5px via `::ng-deep` em todas as partes do `mdc-notched-outline` em `frontend/src/app/shared/components/mes-selector/mes-selector.component.ts`
- [x] T008 [US1] Corrigir overflow do valor do ano (`overflow: visible; text-overflow: unset`) no `.mat-mdc-select-value` via `::ng-deep` em `frontend/src/app/shared/components/mes-selector/mes-selector.component.ts`

**Checkpoint**: Seletor visivelmente menor com bordas pill; navegação entre meses funcionando normalmente

---

## Phase 3: US2 — Data inicial hoje + destaque visual (RF01, RF02, RF05)

**Goal**: Ao carregar, o sistema posiciona o calendário no mês/dia correntes automaticamente, destaca a coluna de hoje visualmente e rola até ela.

**Independent Test**: Abrir o sistema sem nenhuma interação — mês/ano atual exibido, coluna do dia de hoje destacada em laranja, scroll posicionado na coluna de hoje. Navegar para outro mês e recarregar — retorna ao dia atual.

- [x] T009 [US2] Confirmar que `mesAtual: MesAno = { ano: new Date().getFullYear(), mes: new Date().getMonth() + 1 }` está declarado na classe `GradeProducaoComponent` em `frontend/src/app/features/producao/grade-producao/grade-producao.component.ts` (RF01, RF05)
- [x] T010 [US2] Adicionar propriedade `private readonly _hoje = new Date()` e método `eHoje(dia: number): boolean` em `GradeProducaoComponent` em `frontend/src/app/features/producao/grade-producao/grade-producao.component.ts`
- [x] T011 [US2] Adicionar binding `[class.dia-hoje]="eHoje(dia)"` no `<th>` de cabeçalho de dia e nos `<td>` de tbody e tfoot no template de `frontend/src/app/features/producao/grade-producao/grade-producao.component.ts`
- [x] T012 [US2] Adicionar estilos `.dia-hoje { box-shadow: inset 0 -4px 0 0 #ff9800; }` e `tbody .dia-hoje, tfoot .dia-hoje { background-color: rgba(255, 152, 0, 0.08) !important; }` em `frontend/src/app/features/producao/grade-producao/grade-producao.component.ts`
- [x] T013 [US2] Injetar `ElementRef` e adicionar `setTimeout(() => el?.scrollIntoView({behavior:'smooth', block:'nearest', inline:'center'}))` no callback `next` do `ngOnInit` em `frontend/src/app/features/producao/grade-producao/grade-producao.component.ts`
- [x] T014 [P] [US2] Adicionar método `diaSemana(dia: number): string` retornando abreviação pt-BR e exibir `<span class="dia-semana">{{ diaSemana(dia) }}</span><br><span class="num-dia">{{ dia }}</span>` no cabeçalho em `frontend/src/app/features/producao/grade-producao/grade-producao.component.ts`
- [x] T015 [P] [US2] Tornar `.col-nome` sticky (`position: sticky; left: 0; z-index: 2`) e ajustar `z-index` de thead/tfoot em `frontend/src/app/features/producao/grade-producao/grade-producao.component.ts`
- [x] T016 [P] [US2] Implementar optimistic updates (`patchRegistroLocal`, `patchIdLocal`, `removerRegistroLocal`) para evitar reload total da grade após cada save e preservar a posição de scroll em `frontend/src/app/features/producao/grade-producao/grade-producao.component.ts`
- [x] T017 [US2] Adicionar efeito de dimming durante atualização (`.grade-wrapper.atualizando { opacity: 0.35; pointer-events: none; }`) e exibir spinner apenas na carga inicial (`*ngIf="carregando() && !grade()"`) em `frontend/src/app/features/producao/grade-producao/grade-producao.component.ts`

**Checkpoint**: Ao abrir o sistema — mês atual selecionado, dia de hoje destacado em laranja, scroll automático até a coluna de hoje

---

## Phase 4: Polish & Validação

**Purpose**: Verificação cruzada dos cenários do quickstart.md

- [ ] T018 [P] Verificar Cenário 1 do quickstart: abrir o sistema sem nenhuma ação → mês/ano atual exibido, dia de hoje destacado em laranja, scroll posicionado na coluna de hoje
- [ ] T019 [P] Verificar Cenário 2: clicar em `←` e `→` do seletor → navegação funciona; todos os controles visíveis e funcionais
- [ ] T020 [P] Verificar Cenário 3: navegar para mês anterior e recarregar a página → calendário retorna ao mês/dia atual automaticamente
- [ ] T021 [P] Verificar Cenário 4: inspecionar o seletor de mês/ano → visivelmente menor que o original, legível sem zoom, bordas pill, altura compacta

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: Sem dependências — iniciar imediatamente
- **US1 (Phase 2)**: Após T001. T002–T008 no mesmo arquivo — executar em sequência
- **US2 (Phase 3)**: Independente de US1 — pode iniciar após T001. T009–T017 no mesmo componente — executar em sequência
- **Polish (Phase 4)**: Após US1 e US2 completos. Todos em paralelo

### Parallel Opportunities

US1 e US2 operam em **arquivos diferentes** — podem ser implementadas em paralelo após T001:

```
T001 (setup)
├── T002 → T003 → T004 → T005 → T006 → T007 → T008  (mes-selector.component.ts)
└── T009 → T010 → T011 → T012 → T013                 (grade-producao.component.ts)
           └── T014 [P]                                (independente dentro do arquivo)
           └── T015 [P]
           └── T016 [P]
           └── T017
                  ↓
       T018, T019, T020, T021 (verificação — todos em paralelo)
```

---

## Implementation Strategy

### MVP (entrega única — feature é pequena)

1. T001: confirmar ambiente
2. T002–T008: compactar mes-selector
3. T009–T017: inicialização e destaque de hoje
4. T018–T021: verificar todos os cenários
5. Commit
