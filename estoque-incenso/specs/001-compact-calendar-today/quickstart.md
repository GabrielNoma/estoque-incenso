# Quickstart: Calendário Compacto com Data Inicial Hoje

## Arquivos modificados

| Arquivo | Mudança |
|---------|---------|
| `frontend/src/app/shared/components/mes-selector/mes-selector.component.ts` | Gap 8px→2px; widths reduzidos; subscript oculto; altura 34px; bordas pill; borda 1.5px |
| `frontend/src/app/features/producao/grade-producao/grade-producao.component.ts` | `eHoje()`, `diaSemana()`, `.dia-hoje` CSS, scroll to today no `ngOnInit`, optimistic updates |

## Sem mudanças em

- Backend (.NET API)
- Banco de dados (PostgreSQL)
- Serviços Angular (`producao.service.ts`)
- Roteamento, outros componentes

## Como executar

```bash
cd frontend
npm start          # ou: ng serve
```

Acesse `http://localhost:4200` → rota de produção.

## Verificação manual (cenários da spec)

| # | Ação | Resultado esperado |
|---|------|--------------------|
| 1 | Abrir o sistema sem nenhuma interação | Seletor mostra mês/ano atual; coluna do dia de hoje destacada em laranja; scroll posicionado na coluna de hoje |
| 2 | Clicar em "←" ou "→" para navegar de mês | Navegação funciona normalmente; todos os controles visíveis |
| 3 | Navegar para mês anterior e recarregar a página | Retorna ao mês/dia atual |
| 4 | Inspecionar o seletor visualmente | Menor que o original (gap menor, campos mais estreitos, altura 34px, bordas pill) |
| 5 | Editar uma célula de produção | Grade não desaparece durante o save; apenas a célula é atualizada localmente |
