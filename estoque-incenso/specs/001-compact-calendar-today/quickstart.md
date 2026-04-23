# Quickstart: Calendário Compacto com Data Inicial Hoje

## Arquivos a modificar

| Arquivo | Mudança |
|---------|---------|
| `frontend/src/app/shared/components/mes-selector/mes-selector.component.ts` | Compactar estilos inline |
| `frontend/src/app/features/producao/grade-producao/grade-producao.component.ts` | Adicionar método `eHoje(dia)` e classe CSS `dia-hoje` |

## Sem mudanças em

- Backend (.NET API)
- Banco de dados (PostgreSQL)
- Serviços Angular (`producao.service.ts`)
- Roteamento
- Outros componentes

## Como testar manualmente

1. Abrir o sistema no navegador
2. Verificar que o mês/ano exibido é o atual (sem clicar em nada)
3. Verificar que a coluna do dia de hoje está visualmente diferenciada na grade
4. Confirmar que o seletor de mês/ano ocupa menos espaço vertical que antes
5. Navegar para outro mês — confirmar que tudo funciona normalmente
6. Recarregar a página — confirmar que volta para hoje
