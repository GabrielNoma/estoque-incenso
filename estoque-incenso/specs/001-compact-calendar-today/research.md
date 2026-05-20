# Research: Calendário Compacto com Data Inicial Hoje

## Findings

### 1. Inicialização no mês/dia correntes

**Decision:** `GradeProducaoComponent.mesAtual` já é declarado com `new Date()`. `MesSelectorComponent` recebe o valor via `@Input() valor` e sincroniza no `ngOnInit`. RF01 e RF05 satisfeitos desde a estrutura inicial do componente.  
**Rationale:** O pai é dono do estado de navegação; o filho apenas exibe. Fluxo unidirecional Angular (Input → Output) mantido.  
**Alternatives considered:** Persistir última posição navegada no localStorage — descartado pelo RF05 (reload retorna para hoje).

### 2. Destaque visual do dia de hoje

**Decision:** Método `eHoje(dia: number): boolean` no `GradeProducaoComponent` compara `grade().ano/mes` com `new Date()` e aplica classe CSS `dia-hoje` em thead/tbody/tfoot via `[class.dia-hoje]="eHoje(dia)"`.  
**Rationale:** CSS class condicional é o padrão Angular para highlights dinâmicos. Zero dependências novas, solução legível.  
**Alternatives considered:** `mat-badge` ou tooltip — desnecessariamente pesado para um destaque de coluna.

### 3. Scroll automático para hoje no carregamento

**Decision:** `setTimeout(() => el?.scrollIntoView({behavior:'smooth', inline:'center'}))` no callback `next` do subscribe de `ngOnInit`.  
**Rationale:** `*ngFor` renderiza as células _após_ `grade.set(g)` no próximo ciclo de detecção de mudança. `setTimeout` adia o `querySelector('.dia-hoje')` para depois desse ciclo — padrão idiomático Angular.  
**Alternatives considered:** `afterNextRender` + `ChangeDetectorRef.detectChanges()` — mais verboso sem benefício real.

### 4. Compactação via `::ng-deep` com escopo no componente

**Decision:** `::ng-deep` escopado a `.campo-mes` / `.campo-ano` dentro do componente standalone para: ocultar `mat-mdc-form-field-subscript-wrapper`, reduzir altura do `mat-mdc-form-field-flex` para 34 px, aplicar bordas pill (`border-radius: 17px`), borda mais fina (1.5 px).  
**Rationale:** Angular Material MDC 17 não expõe tokens de densidade de form-field granulares o suficiente para esse nível de compactação. `::ng-deep` escopado é a solução padrão documentada para personalização MDC em standalone components.  
**Alternatives considered:** `mat.form-field-density(-2)` no tema global — modifica todos os form-fields do projeto, fora do escopo.

### 5. Optimistic updates para evitar re-scroll

**Decision:** `patchRegistroLocal` / `patchIdLocal` / `removerRegistroLocal` atualizam o signal `grade` localmente; `carregar()` é chamado apenas em erro.  
**Rationale:** Sem optimistic updates, cada save dispararia `carregar()` → `ngOnInit` não é chamado novamente, mas o fato de recarregar a grade reposicionaria o scroll. O patch local mantém o scroll posicionado no dia de hoje após a primeira carga.  
**Alternatives considered:** Flag booleano `jaRolou` para impedir re-scroll — mais estado para gerenciar; patch local resolve o problema de forma mais limpa.

### 6. Arquitetura — zero mudanças no backend

**Decision:** Feature 100% frontend — sem mudanças em API, banco de dados ou serviços Angular.  
**Rationale:** Compactação e destaque de "hoje" são puramente apresentacionais. A API já retorna os dados do mês correto.
