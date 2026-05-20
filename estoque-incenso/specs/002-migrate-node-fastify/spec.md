vamos c# Spec — Migração para Node.js + Fastify + Deploy Render/Supabase

## Visão geral

Migração completa do backend da aplicação EstoqueIncenso de C# .NET para Node.js com Fastify, mantendo todas as funcionalidades existentes sem nenhuma alteração de comportamento para o usuário. O objetivo é simplificar a stack tecnológica, reduzir custo de hospedagem para zero e tornar o deploy automatizado via GitHub Actions com destino ao Render (backend) e Supabase (banco de dados PostgreSQL).

---

## Usuários

- **Gestor:** único usuário da aplicação. Não percebe nenhuma mudança de comportamento — a migração é transparente.

---

## Funcionalidades preservadas (sem alteração de comportamento)

### 1. Cadastro de funcionárias
- Listar, cadastrar, editar nome e ativar/desativar funcionárias.
- Funcionária desativada não aparece na grade, mas mantém histórico.

### 2. Grade de produção diária
- Tabela mensal com funcionárias × dias do mês.
- Células editáveis com quantidade produzida ou marcação de falta.
- Totais por dia, por semana ISO e mensal calculados automaticamente.

### 3. Registro de faltas
- Célula pode ser marcada como falta com motivo: Atestado, Falta ou Outro.
- Motivo "Outro" exige observação em texto livre.
- Falta não entra nos totais de produção.

### 4. Navegação por mês/ano
- Seletor de mês/ano no topo. Mês atual aberto por padrão.
- Qualquer mês histórico pode ser consultado e editado.

### 5. Resumo mensal
- Total produzido por funcionária, total geral da empresa e contagem de faltas com breakdown por motivo.

### 6. Exportação para Excel
- Botão exporta `.xlsx` com aba Produção (grade) e aba Faltas (lista).
- Nome do arquivo: `producao_YYYY_MM.xlsx`.

---

## O que muda nesta migração

### Backend
- **De:** C# .NET Web API + Entity Framework Core + EPPlus + Npgsql
- **Para:** Node.js 20 LTS + Fastify 5 + `pg` (node-postgres, queries SQL raw) + ExcelJS

### Banco de dados
- Schema PostgreSQL idêntico (mesmas tabelas, constraints e índices).
- Script SQL de inicialização substitui as migrations do EF Core.
- Em produção: Supabase (PostgreSQL gerenciado, free tier permanente).

### Frontend
- Angular 17 mantido **sem nenhuma alteração de código**.
- Em produção, o Fastify serve o build compilado do Angular como arquivos estáticos.

### Infraestrutura e deploy
- **De:** execução local / publicação manual
- **Para:** Render (Web Service free tier) + GitHub Actions (CI/CD automático a cada push na `main`)

---

## Contratos de API (todos mantidos, mesmos paths e payloads)

| Método | Path | Descrição |
|--------|------|-----------|
| GET | `/api/funcionarias` | Lista funcionárias (`?incluirInativas=false`) |
| POST | `/api/funcionarias` | Cria funcionária `{ nome }` |
| PUT | `/api/funcionarias/:id` | Atualiza nome `{ nome }` |
| PATCH | `/api/funcionarias/:id/status` | Ativa/desativa `{ ativa }` |
| GET | `/api/registros` | Grade mensal `?ano=&mes=` |
| PUT | `/api/registros` | Upsert registro diário |
| DELETE | `/api/registros/:id` | Remove registro (limpa célula) |
| GET | `/api/exportacao/excel` | Exporta `.xlsx` `?ano=&mes=` |

---

## Estrutura de pastas alvo

```
estoque-incenso/
  backend/                  ← Node.js/Fastify (substitui o C# inteiro)
    src/
      routes/
        funcionarias.js
        registros.js
        exportacao.js
      plugins/
        db.js               ← pool de conexão pg
        cors.js
        static.js           ← serve o build do Angular
      db/
        schema.sql          ← script de criação do banco
      app.js                ← instância Fastify + plugins + rotas
    server.js               ← entrypoint (listen)
    package.json
  frontend/                 ← Angular 17 (sem alterações)
  .github/
    workflows/
      deploy.yml            ← build Angular → deploy Render via Deploy Hook
```

---

## Infraestrutura de deploy

### Supabase (banco de dados)
- PostgreSQL free tier (500 MB, sem expiração).
- Conexão via variável de ambiente `DATABASE_URL`.
- Schema inicializado manualmente via `schema.sql` na primeira execução.

### Render (hospedagem do backend)
- Web Service free tier.
- Deploy disparado automaticamente pelo GitHub Actions via Deploy Hook (URL secreta do Render).
- Variável de ambiente `DATABASE_URL` configurada no painel do Render.
- Em produção, o servidor Node.js serve `/api/*` (API) e `/*` (Angular estático).
- **Limitação conhecida:** serviço hiberna após 15 min de inatividade; primeira requisição pode levar ~30 s para acordar.

### GitHub Actions (CI/CD)
- Pipeline acionado em push para `main`.
- Etapas: instalar dependências → rodar testes → build do Angular → acionar Deploy Hook do Render.

---

## Regras de negócio (mantidas)

- Célula não pode ter produção e falta simultaneamente.
- Se `falta = true`, motivo é obrigatório.
- Se motivo = `Outro`, observação é obrigatória e não pode ser vazia.
- Quantidade deve ser ≥ 0.
- Nome de funcionária é único.
- Sem autenticação: sistema de uso interno/local.

---

## Fora do escopo desta migração

- Alterações visuais ou funcionais no frontend Angular.
- Mudança no schema do banco PostgreSQL.
- Autenticação ou controle de acesso.
- Alteração nos contratos de API (paths, métodos, payloads, responses).
- Migração de dados históricos (banco já existe localmente; Supabase receberá schema limpo ou dump manual).

---

## Critérios de aceite

- [ ] Todos os endpoints da API respondem com os mesmos payloads da versão C#.
- [ ] Grade de produção carrega, salva e exclui registros corretamente via novo backend.
- [ ] Exportação Excel gera arquivo `.xlsx` com abas Produção e Faltas idênticas ao comportamento atual.
- [ ] Frontend Angular funciona sem nenhuma alteração de código apontando para o novo backend.
- [ ] Push para `main` aciona o pipeline do GitHub Actions e faz deploy automático no Render.
- [ ] Aplicação fica acessível via URL pública do Render após o deploy.
- [ ] Banco Supabase conecta corretamente via `DATABASE_URL` em produção.

---

## Premissas e dependências

- O schema do banco não muda; o `schema.sql` é equivalente às migrations atuais do EF Core.
- O gestor aceita a limitação de cold start (~30 s) do Render free tier.
- O repositório GitHub já existe e tem Actions habilitado.
- Dump/migração de dados históricos é responsabilidade do gestor (fora do escopo técnico desta migração).
