# Research: Calendário Compacto com Data Inicial Hoje

## Findings

### 1. Estado atual do `mes-selector`

**Decision:** O componente já inicializa com o mês/ano correntes via `new Date()`.
**Rationale:** `mesAtual` em `grade-producao.component.ts` (linha 105) e o `@Input() valor` em `mes-selector.component.ts` (linha 48) ambos usam `new Date()`. RF01 e RF05 já estão satisfeitos.
**Alternatives considered:** Persistir última posição navegada no localStorage — descartado pela spec (RF05: reload retorna para hoje).

### 2. Destaque visual do dia de hoje

**Decision:** Adicionar classe CSS `dia-hoje` na célula da grade cujo número de dia corresponde a `new Date().getDate()` quando o mês/ano carregado for o mês/ano atual.
**Rationale:** Padrão adotado em calendários web — CSS class condicional no template `*ngFor` da grade de dias. Solução simples, zero dependências novas.
**Alternatives considered:** Angular Material `mat-badge` ou tooltip — desnecessariamente pesado para um destaque simples de coluna.

### 3. Compactação do `mes-selector`

**Decision:** Reduzir `campo-mes` de 140px → 110px, `campo-ano` de 90px → 72px, e adicionar `subscriptSizing: fixed` / `dense` para remover o espaço de subscript reservado pelo `mat-form-field` (principal responsável pelo tamanho excessivo).
**Rationale:** O Angular Material `mat-form-field` reserva ~20px de altura extra abaixo do campo para mensagens de validação. Para campos sem validação, `subscriptSizing: "fixed"` e a remoção do padding inferior elimina esse espaço. Aplicar `appearance="outline"` com padding customizado reduz a altura total do campo.
**Alternatives considered:**
- Usar `mat-chip` ou botão com texto em vez de `mat-select` — mudaria o UX de forma mais invasiva, fora do escopo.
- Mudar para `appearance="fill"` — visualmente diferente e não necessariamente mais compacto.

### 4. Arquitetura de mudança — sem backend

**Decision:** Feature é 100% frontend — zero mudanças no backend, API ou banco de dados.
**Rationale:** Compactação visual e destaque de "hoje" são puramente apresentacionais. A API já retorna os dados do mês correto; o que muda é apenas como o frontend os exibe.
