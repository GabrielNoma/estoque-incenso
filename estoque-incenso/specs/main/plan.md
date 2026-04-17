# Implementation Plan: Controle de Produção Diária

**Branch**: `main` | **Date**: 2026-04-17 | **Spec**: [spec.md](../../.specify/templates/spec-template.md)
**Input**: Feature specification from `.specify/templates/spec-template.md`

## Summary

Sistema web (Angular 17 + .NET 8 Web API + PostgreSQL) para registrar a produção diária de funcionárias
de uma empresa familiar de incenso. O gestor acessa via navegador em rede local, digita quantidades numa
grade mensal interativa e exporta relatórios `.xlsx`. Sem autenticação — sistema de uso único local.

## Technical Context

**Language/Version**: C# (.NET 8), TypeScript (Angular 17)
**Primary Dependencies**: Angular 17, Angular Material, .NET 8 Web API, Entity Framework Core 8, EPPlus 7, PostgreSQL 16, Npgsql
**Storage**: PostgreSQL 16
**Testing**: xUnit + Testcontainers (backend), Jasmine + Karma (Angular)
**Target Platform**: Navegador web moderno em rede local Windows
**Project Type**: Web application — Angular SPA + .NET REST API
**Performance Goals**: Único usuário simultâneo, rede local — sem requisito estrito de latência
**Constraints**: Sem autenticação; IP direto na rede local; PostgreSQL rodando localmente
**Scale/Scope**: 6–15 funcionárias, 1 gestor, ~300 registros/mês

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Princípio | Gate | Status |
|-----------|------|--------|
| I. Simplicidade de Uso | REST direto sem over-engineering; grade Angular com `<input>` nativo; sem libs de state management pesadas | [x] PASS |
| II. Clean Code & SOLID | Backend: Controller → Service → Repository (SRP, DI); Frontend: Component → Service (HTTP); nenhuma lógica de negócio em Controllers ou Components | [x] PASS |
| III. Observabilidade de Erros | Backend: `ILogger<T>` em todos os Services + `ExceptionHandlerMiddleware` global; Frontend: `HttpInterceptor` para erros de rede + toast de feedback ao usuário | [x] PASS |

*Violações DEVEM ser documentadas na tabela Complexity Tracking com justificativa.*

## Project Structure

### Documentation (this feature)

```text
specs/main/
├── plan.md              # Este arquivo
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
└── contracts/
    ├── funcionarias.md
    ├── registros.md
    └── exportacao.md
```

### Source Code (repository root)

```text
backend/
├── EstoqueIncenso.Api/
│   ├── Controllers/
│   │   ├── FuncionariasController.cs
│   │   ├── RegistrosController.cs
│   │   └── ExportacaoController.cs
│   ├── Middleware/
│   │   └── ExceptionHandlerMiddleware.cs
│   └── Program.cs
├── EstoqueIncenso.Application/
│   ├── Services/
│   │   ├── FuncionariaService.cs
│   │   ├── RegistroService.cs
│   │   └── ExportacaoService.cs
│   └── DTOs/
│       ├── FuncionariaDto.cs
│       ├── RegistroDiarioDto.cs
│       └── GradeMensalDto.cs
├── EstoqueIncenso.Domain/
│   ├── Entities/
│   │   ├── Funcionaria.cs
│   │   └── RegistroDiario.cs
│   └── Enums/
│       └── MotivoFalta.cs
├── EstoqueIncenso.Infrastructure/
│   ├── Data/
│   │   ├── AppDbContext.cs
│   │   └── Migrations/
│   └── Repositories/
│       ├── FuncionariaRepository.cs
│       └── RegistroRepository.cs
└── EstoqueIncenso.Tests/
    ├── Unit/
    └── Integration/

frontend/
├── src/
│   ├── app/
│   │   ├── features/
│   │   │   ├── funcionarias/
│   │   │   │   ├── funcionarias.component.ts
│   │   │   │   ├── funcionarias.component.html
│   │   │   │   └── funcionarias.service.ts
│   │   │   └── producao/
│   │   │       ├── grade-producao/
│   │   │       │   ├── grade-producao.component.ts
│   │   │       │   └── grade-producao.component.html
│   │   │       ├── celula-producao/
│   │   │       │   └── celula-producao.component.ts
│   │   │       ├── dialogo-falta/
│   │   │       │   └── dialogo-falta.component.ts
│   │   │       └── producao.service.ts
│   │   ├── shared/
│   │   │   ├── interceptors/
│   │   │   │   └── error.interceptor.ts
│   │   │   └── components/
│   │   │       └── mes-selector/
│   │   │           └── mes-selector.component.ts
│   │   └── app.routes.ts
│   └── environments/
│       ├── environment.ts
│       └── environment.prod.ts
└── ...
```

**Structure Decision**: Web application — Angular SPA em `frontend/`, .NET 8 Web API em `backend/`.
Dois projetos justificados pela separação de tecnologias (TypeScript vs C#) e responsabilidades
(UI vs API). Quatro projetos C# (Api, Application, Domain, Infrastructure) justificados — ver
Complexity Tracking.

## Complexity Tracking

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| 4 projetos C# (Api, Application, Domain, Infrastructure) | Testabilidade: Services testados sem subir o host HTTP; isolamento do EF Core nos testes de unidade | 1 projeto único mistura acesso a dados com lógica de negócio — Services não podem ser testados sem banco real |
