# Research: Controle de Produção Diária

## Decisões técnicas resolvidas

### 1. Estratégia de auto-save na grade

**Decision**: Auto-save por `blur` + debounce de 500ms — ao sair da célula (ou pressionar Enter),
dispara `PATCH /api/registros` para o registro individual.

**Rationale**: Evita botão "Salvar" que pode ser esquecido; debounce previne requisições em cascata
durante digitação rápida; falha de rede exibe toast de erro e restaura o valor anterior na célula.

**Alternatives considered**:
- Botão salvar global: descartado — usuário pode fechar o navegador sem salvar
- Auto-save em cada tecla (`keyup`): descartado — gera muitas requisições desnecessárias

---

### 2. Totais semanais em meses com semanas parciais

**Decision**: Semanas exibidas como colunas agrupadas por semana ISO (segunda a domingo).
Quando uma semana ISO atravessa dois meses, a coluna de total semanal soma apenas os dias
**do mês exibido** — dias do outro mês são ignorados.

**Rationale**: O gestor visualiza um mês por vez; incluir dias de outro mês na soma seria confuso.
O cabeçalho da coluna mostra `Sem. N` (semana do mês, 1-based) para deixar claro.

**Alternatives considered**:
- Semanas ISO completas (mesmo com dias de outro mês): descartado — confunde totais
- Sem coluna de total semanal: descartado — está no spec

---

### 3. Componente de grade Angular

**Decision**: HTML `<table>` nativo com `<input type="number">` por célula. Sem libs de grid
externas (ag-Grid, etc.).

**Rationale**: ~15 funcionárias × ~23 dias úteis = ~345 células — volume pequeno que não justifica
lib pesada. `<input>` nativo simplifica binding Angular e acessibilidade.

**Alternatives considered**:
- `contenteditable` em `<td>`: descartado — binding Angular e validação mais complexos
- ag-Grid / DevExtreme: descartado — over-engineering para o volume de dados

---

### 4. Feedback de erro de rede no frontend

**Decision**: `HttpInterceptor` global captura todos os erros HTTP e exibe `MatSnackBar` com
mensagem descritiva. O componente de célula mantém o valor anterior em memória para rollback
em caso de falha de save.

**Rationale**: Satisfaz Princípio III (Observabilidade de Erros) — usuário vê feedback imediato;
o log do backend registra o erro com contexto completo.

---

### 5. Campo `observacao_falta` quando motivo = "outro"

**Decision**: Campo obrigatório quando `motivo_falta = outro`, max 500 caracteres.
Validação no frontend (reactive form) e no backend (FluentValidation ou DataAnnotations).

**Alternatives considered**:
- Campo opcional: descartado — "outro" sem descrição não tem utilidade para o relatório

---

### 6. Exportação Excel — biblioteca

**Decision**: EPPlus 7 (LGPLv2.1 com opção de licença comercial). Gerado no backend,
retornado como `application/vnd.openxmlformats-officedocument.spreadsheetml.sheet`.

**Rationale**: Especificado no spec. EPPlus 7 é maduro, tem boa documentação e suporte
a formatação de células (cor para fim de semana/falta).

---

### 7. CORS — configuração para rede local

**Decision**: Backend configurado com `AllowAnyOrigin` em desenvolvimento e com origin
específica (IP:porta do Angular dev server) em produção local.

**Rationale**: Sistema roda em rede local sem domínio fixo — origin pode variar pelo IP da máquina.
Em produção local, Angular é servido pelo próprio .NET como arquivo estático (publish output).
