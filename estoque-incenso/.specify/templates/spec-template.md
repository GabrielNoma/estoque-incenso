# Spec — Controle de Produção Diária

## Visão geral

Sistema web para registrar e acompanhar a produção diária de funcionárias em uma pequena empresa familiar de incenso e produtos de limpeza energética. Substitui uma planilha manual mantida pelo gestor, com foco em entrada rápida de dados, visualização clara e exportação para Excel.

---

## Usuários

- **Gestor (pai):** único usuário. Entra os dados diariamente, consulta totais e exporta relatórios.
- **Funcionárias:** 6 a 15 pessoas. Aparecem no sistema pelo nome, não acessam o sistema diretamente.

---

## Funcionalidades

### 1. Cadastro de funcionárias
- Adicionar, editar e desativar funcionárias (nome).
- Funcionária desativada não aparece na grade diária, mas mantém histórico.

### 2. Grade de produção diária
- Tela principal: tabela com **uma linha por funcionária** e **uma coluna por dia do mês**.
- Célula editável em linha: gestor clica na célula do dia e digita a quantidade produzida.
- Células do fim de semana são marcadas visualmente (desabilitadas por padrão, mas editáveis se necessário).
- Linha de **total do dia** (soma de todas as funcionárias naquele dia) na linha de rodapé.
- Coluna de **total mensal** por funcionária na última coluna.
- Coluna de **total semanal** por funcionária (agrupado por semana ISO).

### 3. Registro de faltas
- Em vez de um número, a célula de um dia pode ser marcada como falta.
- Ao marcar como falta, abrir um seletor com o motivo:
  - **Atestado** (médico)
  - **Falta** (comum, injustificada)
  - **Outro** (campo de texto livre)
- Falta é exibida na célula com ícone ou cor diferente (não entra na soma de produção).
- Relatório de faltas do mês visível por funcionária.

### 4. Navegação por mês
- Seletor mês/ano no topo da tela.
- Histórico completo disponível para consulta — qualquer mês passado pode ser aberto e editado.
- Mês atual aberto por padrão ao entrar no sistema.

### 5. Resumo mensal
- Painel com os totais do mês corrente (ou do mês selecionado):
  - Total produzido por funcionária
  - Total geral da empresa no mês
  - Quantidade de faltas por funcionária (com breakdown por motivo)

### 6. Exportação para Excel
- Botão "Exportar Excel" gera uma planilha `.xlsx` com:
  - Aba **Produção:** grade idêntica à tela (funcionária × dia, totais por semana, total mensal).
  - Aba **Faltas:** lista de faltas do mês com funcionária, data e motivo.
- Nome do arquivo sugerido: `producao_YYYY_MM.xlsx`.

---

## Regras de negócio

- Dias sem registro (nem produção nem falta) são tratados como vazios — não entram nos totais.
- Total semanal considera apenas dias úteis registrados (segunda a sexta por padrão).
- Uma célula não pode ter produção e falta ao mesmo tempo.
- Não há autenticação: sistema roda em rede local, acessado diretamente pelo navegador.

---

## Stack técnica

| Camada | Tecnologia |
|---|---|
| Frontend | Angular + SCSS |
| Backend | .NET Web API (C#) |
| Banco de dados | PostgreSQL |
| ORM | Entity Framework Core |
| Export Excel | biblioteca EPPlus (backend) |

---

## Fora do escopo

- Login / controle de acesso
- Múltiplos usuários simultâneos
- Metas de produção ou indicadores de desempenho
- Integração com folha de pagamento
- App mobile

---

## Modelo de dados (rascunho)

```
Funcionaria
  id, nome, ativa

RegistroDiario
  id, funcionaria_id, data (DATE), quantidade (nullable), falta (bool), motivo_falta (enum: atestado | falta | outro | null), observacao_falta (nullable text)
```

---

## Critérios de aceite (principais)

- [ ] Gestor consegue abrir o mês atual e digitar a produção de cada funcionária em cada dia sem sair da tela.
- [ ] Ao marcar falta, o sistema pede o motivo antes de salvar.
- [ ] Totais por dia, por semana e por mês são calculados automaticamente e visíveis na mesma tela.
- [ ] Exportação gera um `.xlsx` legível diretamente no Excel/LibreOffice.
- [ ] É possível consultar qualquer mês anterior sem perda de dados.
