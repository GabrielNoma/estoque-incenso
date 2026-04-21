---
description: "Task list — Controle de Produção Diária"
---

# Tasks: Controle de Produção Diária

**Input**: Design documents from `specs/main/`
**Prerequisites**: plan.md ✅, data-model.md ✅, contracts/ ✅, research.md ✅, quickstart.md ✅

**Testes**: não solicitados explicitamente — omitidos (adicionar com `/speckit-tasks` se desejado).

**Organização**: tasks agrupadas por user story para entrega incremental independente.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: pode rodar em paralelo (arquivos diferentes, sem dependência)
- **[Story]**: user story da tarefa (US1–US6)

---

## Phase 1: Setup (Infraestrutura do Projeto)

**Objetivo**: criar esqueleto do projeto antes de qualquer implementação.

- [X] T001 Criar solução .NET 8 com 4 projetos: `EstoqueIncenso.Api`, `EstoqueIncenso.Application`, `EstoqueIncenso.Domain`, `EstoqueIncenso.Infrastructure` em `backend/` ✅ (net10.0; refs + NuGet: EFCore, Npgsql, EPPlus, EFCore.Design)
- [X] T002 Criar projeto Angular 17 com Angular Material em `frontend/` via `ng new` ✅ (Angular 17.3 + @angular/material@17 + @angular/cdk@17 instalados)
- [X] T003 Configurar string de conexão PostgreSQL em `backend/EstoqueIncenso.Api/appsettings.Development.json` e `appsettings.json` ✅
- [X] T004 [P] Configurar CORS em `backend/EstoqueIncenso.Api/Program.cs` (AllowAnyOrigin em dev, origin específica em prod)
- [X] T005 [P] Configurar environments Angular em `frontend/src/environments/environment.ts` e `environment.prod.ts` com `apiUrl`

---

## Phase 2: Foundation (Pré-requisitos bloqueantes)

**Objetivo**: infraestrutura compartilhada que TODAS as user stories dependem.

**⚠️ CRÍTICO**: nenhuma user story pode ser iniciada antes desta fase estar completa.

- [X] T006 [P] Criar entidade `Funcionaria` em `backend/EstoqueIncenso.Domain/Entidades/Funcionaria.cs` (Id, Nome, Ativa)
- [X] T007 [P] Criar entidade `RegistroDiario` em `backend/EstoqueIncenso.Domain/Entidades/RegistroDiario.cs` (Id, FuncionariaId, Data, Quantidade, Falta, MotivoFalta, ObservacaoFalta)
- [X] T008 [P] Criar enum `MotivoFalta` em `backend/EstoqueIncenso.Domain/Enums/MotivoFalta.cs` (Atestado=1, Falta=2, Outro=3)
- [X] T009 Criar `ContextoBancoDados` em `backend/EstoqueIncenso.Infrastructure/Dados/ContextoBancoDados.cs` com mapeamento EF Core, unique constraint `(FuncionariaId, Data)` e CHECK constraints do data-model
- [X] T010 Criar e aplicar migration inicial via EF Core: `dotnet ef migrations add InitialSchema --project EstoqueIncenso.Infrastructure --startup-project EstoqueIncenso.Api` ✅ (HasColumnName() snake_case adicionado; migration recriada e aplicada)
- [X] T011 Criar `MidlwareExcecoes` em `backend/EstoqueIncenso.Api/Middleware/MidlwareExcecoes.cs` com `ILogger` — log de exceção + response JSON padronizado (Constituição Princípio III)
- [X] T012 Registrar middleware, CORS, DbContext e serviços de DI em `backend/EstoqueIncenso.Api/Program.cs`
- [X] T013 [P] Criar `ErrorInterceptor` Angular em `frontend/src/app/shared/interceptors/error.interceptor.ts` — captura erros HTTP e exibe `MatSnackBar` (Constituição Princípio III)
- [X] T014 [P] Registrar `ErrorInterceptor` como `HTTP_INTERCEPTORS` em `frontend/src/app/app.config.ts`

**Checkpoint**: Foundation completa — user stories podem ser iniciadas em paralelo.

---

## Phase 3: User Story 1 — Cadastro de Funcionárias (Priority: P1) 🎯 MVP

**Goal**: gestor consegue cadastrar, editar e desativar funcionárias pelo nome.

**Independent Test**: Abrir a tela de Funcionárias → adicionar "Ana Silva" → verificar que aparece na lista → desativar → verificar que some da lista ativa. Funciona sem nenhuma outra feature.

### Backend

- [X] T015 [P] [US1] Criar `RepositorioFuncionaria` em `backend/EstoqueIncenso.Infrastructure/Repositorios/RepositorioFuncionaria.cs` (ListarAsync, BuscarPorIdAsync, CriarAsync, AtualizarAsync) com `ILogger`
- [X] T016 [P] [US1] Criar `FuncionariaDto`, `CriarFuncionariaDto`, `AtualizarFuncionariaDto`, `AtualizarStatusDto` em `backend/EstoqueIncenso.Application/DTOs/FuncionariaDto.cs`
- [X] T017 [US1] Criar `ServicoFuncionaria` em `backend/EstoqueIncenso.Application/Servicos/ServicoFuncionaria.cs` (listar, criar, atualizar, ativar/desativar) com `ILogger` — validação de nome duplicado retorna erro descritivo
- [X] T018 [US1] Criar `ControladorFuncionarias` em `backend/EstoqueIncenso.Api/Controladores/ControladorFuncionarias.cs` com rotas: `GET /api/funcionarias`, `POST /api/funcionarias`, `PUT /api/funcionarias/{id}`, `PATCH /api/funcionarias/{id}/status`

### Frontend

- [X] T019 [P] [US1] Criar `FuncionariaService` Angular em `frontend/src/app/features/funcionarias/funcionarias.service.ts` — métodos: listar, criar, atualizar, alternarStatus (HTTP calls para API)
- [X] T020 [US1] Criar `FuncionariasComponent` em `frontend/src/app/features/funcionarias/funcionarias.component.ts` — lista de funcionárias com `MatTable`, `MatDialog` para criar/editar (`DialogoFuncionariaComponent`), toggle ativar/desativar

**Checkpoint**: US1 independentemente funcional e testável.

---

## Phase 4: User Story 2 — Grade de Produção Diária (Priority: P2) 🎯 Core

**Goal**: gestor vê a grade mensal com linhas por funcionária e colunas por dia; digita produção nas células; totais calculados automaticamente.

**Independent Test**: Abrir a tela principal → grade mostra funcionárias × dias do mês → clicar numa célula → digitar 45 → Tab/Enter → célula salva e total do dia atualiza. Funciona após US1.

### Backend

- [X] T021 [P] [US2] Criar `RepositorioRegistro` em `backend/EstoqueIncenso.Infrastructure/Repositorios/RepositorioRegistro.cs` (ListarPorMesAsync, BuscarPorFuncionariaEDataAsync, CriarOuAtualizarAsync, ExcluirAsync) com `ILogger`
- [X] T022 [P] [US2] Criar DTOs: `RegistroDiarioDto`, `UpsertRegistroDto`, `GradeMensalDto`, `FuncionariaComRegistrosDto`, `RegistroSalvoDto` em `backend/EstoqueIncenso.Application/DTOs/RegistroDto.cs`
- [X] T023 [US2] Criar `ServicoRegistro` em `backend/EstoqueIncenso.Application/Servicos/ServicoRegistro.cs` — lógica de upsert com validação de exclusividade quantidade/falta; montagem do `GradeMensalDto`; interface `IServicoRegistro` em `Interfaces/`; com `ILogger`
- [X] T024 [US2] Criar `ControladorRegistros` em `backend/EstoqueIncenso.Api/Controladores/ControladorRegistros.cs` com rotas: `GET /api/registros?ano=&mes=`, `PUT /api/registros`, `DELETE /api/registros/{id}`

### Frontend

- [X] T025 [P] [US2] Criar `ProducaoService` Angular em `frontend/src/app/features/producao/producao.service.ts` — getGrade(ano, mes), upsertRegistro, deleteRegistro ✅
- [X] T026 [P] [US2] Criar `MesSelectorComponent` em `frontend/src/app/shared/components/mes-selector/mes-selector.component.ts` — seletor mês/ano com `MatSelect`, emite evento ao mudar ✅
- [X] T027 [US2] Criar `CelulaProducaoComponent` em `frontend/src/app/features/producao/celula-producao/celula-producao.component.ts` — `<input type="number">` com auto-save em `blur` (debounce 500ms), mantém valor anterior para rollback em caso de erro de rede ✅
- [X] T028 [US2] Criar `GradeProducaoComponent` em `frontend/src/app/features/producao/grade-producao/grade-producao.component.ts` e `.html` — tabela `<mat-table>` ou `<table>` com: linhas por funcionária ativa, colunas por dia do mês, colunas de total semanal, coluna de total mensal, linha de total do dia no rodapé; fim de semana com estilo visual diferenciado ✅

**Checkpoint**: US1 + US2 independentemente funcionais.

---

## Phase 5: User Story 3 — Registro de Faltas (Priority: P3)

**Goal**: célula pode ser marcada como falta com motivo (atestado / falta / outro + texto); falta exibida visualmente diferente e não entra na soma.

**Independent Test**: Na grade → clicar no ícone de falta de uma célula → diálogo abre → selecionar "Atestado" → confirmar → célula exibe ícone/cor de falta → total do dia NÃO muda.

- [X] T029 [P] [US3] Criar `DialogoFaltaComponent` em `frontend/src/app/features/producao/dialogo-falta/dialogo-falta.component.ts` — `MatDialog` com `MatRadioGroup` para motivo (Atestado, Falta, Outro) e `MatInput` para observação (obrigatório quando Outro, max 500 chars); reactive form com validação ✅
- [X] T030 [US3] Integrar `DialogoFaltaComponent` ao `CelulaProducaoComponent`: botão de falta na célula abre o diálogo; ao confirmar chama `ProducaoService.upsertRegistro` com `falta: true`; célula exibe "FALTA" com cor/ícone diferenciado e não mostra input numérico ✅
- [X] T031 [US3] Adicionar relatório de faltas do mês por funcionária no `GradeProducaoComponent` ou painel lateral: lista com funcionária, data e motivo ✅ (incluído no ResumoMensalComponent)

**Checkpoint**: US1 + US2 + US3 independentemente funcionais.

---

## Phase 6: User Story 4 — Navegação por Mês (Priority: P4)

**Goal**: gestor pode selecionar qualquer mês/ano e a grade recarrega com os dados daquele período; mês atual aberto por padrão.

**Independent Test**: Grade aberta no mês atual → usar seletor → selecionar mês anterior → grade recarrega com dados históricos → editar uma célula → valor persiste ao voltar para o mesmo mês.

- [X] T032 [US4] Conectar `MesSelectorComponent` ao `GradeProducaoComponent` em `frontend/src/app/features/producao/grade-producao/grade-producao.component.ts` — ao mudar mês/ano: chamar `ProducaoService.getGrade(ano, mes)` e renderizar nova grade; inicializar com mês/ano atual ✅
- [X] T033 [US4] Garantir que o backend suporte edição de meses passados: `RegistroService.Upsert` não deve restringir por data — qualquer mês pode ser editado (verificar sem restrição de data no service) ✅ (verificado — sem restrição de data)

**Checkpoint**: US1–US4 independentemente funcionais; grade completa e navegável.

---

## Phase 7: User Story 5 — Resumo Mensal (Priority: P5)

**Goal**: painel exibe totais consolidados do mês: total produzido por funcionária, total geral, faltas com breakdown por motivo.

**Independent Test**: Grade de abril exibida → painel de resumo mostra: total de Ana = 850, total geral = 1470, Ana: 1 atestado.

- [X] T034 [P] [US5] Criar `ResumoMensalComponent` em `frontend/src/app/features/producao/resumo-mensal/resumo-mensal.component.ts` e `.html` — exibe: tabela de total por funcionária, total geral da empresa, tabela de faltas por funcionária com breakdown (atestado / falta / outro); atualiza automaticamente quando grade muda ✅
- [X] T035 [US5] Calcular totais de resumo no frontend a partir do `GradeMensalDto` já retornado pelo `GET /api/registros` — sem endpoint adicional necessário ✅

**Checkpoint**: US1–US5 independentemente funcionais.

---

## Phase 8: User Story 6 — Exportação para Excel (Priority: P6)

**Goal**: botão "Exportar Excel" gera `.xlsx` com aba Produção (grade) e aba Faltas (lista), com nome `producao_YYYY_MM.xlsx`.

**Independent Test**: Grade de abril exibida → clicar "Exportar Excel" → arquivo `producao_2026_04.xlsx` baixado → abrir no LibreOffice: aba Produção com grade formatada (fins de semana cinza, faltas amarelo), aba Faltas com lista.

### Backend

- [X] T036 [P] [US6] Criar `ExportacaoService` em `backend/EstoqueIncenso.Application/Servicos/ServicoExportacao.cs` usando EPPlus 8.5.3: aba Produção (grade funcionária×dia com totais, estilo: fim de semana cinza, falta amarelo, total negrito), aba Faltas (lista com funcionária, data, motivo, observação) com `ILogger` ✅
- [X] T037 [US6] Criar `ControladorExportacao` em `backend/EstoqueIncenso.Api/Controladores/ControladorExportacao.cs` com rota `GET /api/exportacao/excel?ano=&mes=` — retorna `FileContentResult` com Content-Type `application/vnd.openxmlformats-officedocument.spreadsheetml.sheet` e Content-Disposition com nome sugerido ✅

### Frontend

- [X] T038 [US6] Criar `ExportacaoService` Angular em `frontend/src/app/features/producao/exportacao/exportacao.service.ts` — chamada HTTP com `responseType: 'blob'` e trigger de download no browser; botão "Exportar Excel" no `GradeProducaoComponent` ✅

**Checkpoint**: todas as 6 user stories funcionais e independentemente testáveis.

---

## Phase N: Polish & Cross-Cutting Concerns

**Objetivo**: refinamentos visuais, publicação e conformidade constitucional.

- [X] T039 [P] Adicionar estilo SCSS para fins de semana na grade (fundo cinza claro `#f5f5f5`) e para células de falta (fundo amarelo `#fff9c4`) — implementado inline nos componentes ✅
- [X] T040 [P] Configurar Angular production build copiando `dist/` para `backend/EstoqueIncenso.Api/wwwroot/` conforme `quickstart.md` — serve estático via .NET configurado com `UseDefaultFiles` + `UseStaticFiles` + `MapFallbackToFile` ✅
- [X] T041 Revisão de conformidade constitucional: todos os Controllers são finos, todos os Services têm `ILogger<T>`, nenhum catch vazio ✅ (verificado por agente de backend)
- [ ] T042 [P] Validar checklist completo do `specs/main/quickstart.md` — executar todos os 7 critérios de aceite manualmente

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: sem dependências — pode iniciar imediatamente
- **Foundation (Phase 2)**: depende de Setup — **BLOQUEIA todas as user stories**
- **US1 (Phase 3)**: depende de Foundation — primeira a ser implementada
- **US2 (Phase 4)**: depende de US1 (precisa de funcionárias cadastradas para popular a grade)
- **US3 (Phase 5)**: depende de US2 (extensão da grade)
- **US4 (Phase 6)**: depende de US2 (extensão da grade — navegação por mês)
- **US5 (Phase 7)**: depende de US2 (usa dados da grade)
- **US6 (Phase 8)**: depende de US2 (exporta dados da grade); pode ser desenvolvida em paralelo com US3–US5
- **Polish (Phase N)**: depende de todas as user stories desejadas

### Within Each User Story

- Entidades Domain → Repository → Service → Controller (backend)
- Service Angular → Components (frontend)
- Backend e frontend de uma mesma story podem rodar em paralelo

### Parallel Opportunities

```bash
# Phase 2: Foundation — rodar em paralelo
Task: T006 Criar entidade Funcionaria
Task: T007 Criar entidade RegistroDiario
Task: T008 Criar enum MotivoFalta
Task: T013 Criar ErrorInterceptor Angular

# Phase 3: US1 — backend e frontend em paralelo após T018
Task: T015 FuncionariaRepository (backend)
Task: T016 FuncionariaDto (backend)
Task: T019 FuncionariaService Angular (frontend)

# Phase 4: US2 — backend e frontend em paralelo após T024
Task: T021 RegistroRepository (backend)
Task: T022 RegistroDiarioDto (backend)
Task: T025 ProducaoService Angular (frontend)
Task: T026 MesSelectorComponent (frontend)
```

---

## Implementation Strategy

### MVP (US1 + US2)

1. Completar Phase 1: Setup
2. Completar Phase 2: Foundation (CRÍTICO — bloqueia tudo)
3. Completar Phase 3: US1 — Cadastro de Funcionárias
4. Completar Phase 4: US2 — Grade de Produção
5. **PARAR e VALIDAR**: testar independentemente US1 + US2
6. Sistema já entrega valor: gestor cadastra funcionárias e registra produção diária

### Incremental Delivery

1. Setup + Foundation → base pronta
2. US1 → cadastrar funcionárias (MVP parcial)
3. US2 → grade de produção (MVP completo — entrega valor imediato)
4. US3 → faltas (melhora US2)
5. US4 → navegação por mês (melhora US2)
6. US5 → resumo mensal
7. US6 → exportação Excel

---

## Notes

- `[P]` = arquivos diferentes, sem dependência — podem rodar em paralelo
- Backend e frontend de uma mesma story podem ser desenvolvidos em paralelo (contratos definidos)
- Constituição Princípio III exige `ILogger` em TODO service e middleware global — não opcional
- Auto-save na célula (blur + debounce 500ms) implementado em `CelulaProducaoComponent` com rollback
- Totais calculados no backend (`RegistroService`) e enviados no `GradeMensalDto` — frontend não recalcula
- Não há autenticação — sistema de rede local, acesso direto pelo IP
