# Quickstart: Controle de Produção Diária

## Pré-requisitos

- .NET 8 SDK
- Node.js 20+ e npm
- PostgreSQL 16 rodando localmente
- Angular CLI (`npm install -g @angular/cli`)

---

## 1. Backend

```bash
cd backend/EstoqueIncenso.Api

# Copiar e editar connection string
cp appsettings.Development.json.example appsettings.Development.json
# Editar: "DefaultConnection": "Host=localhost;Database=estoque_incenso;Username=postgres;Password=SUA_SENHA"

# Criar banco e rodar migrations
dotnet ef database update --project ../EstoqueIncenso.Infrastructure

# Subir a API (porta 5000)
dotnet run
```

API disponível em: `http://localhost:5000`
Swagger UI: `http://localhost:5000/swagger`

---

## 2. Frontend

```bash
cd frontend

npm install

# Verificar src/environments/environment.ts:
# apiUrl: 'http://localhost:5000/api'

ng serve
```

App disponível em: `http://localhost:4200`

---

## 3. Validação do fluxo principal

1. Abrir `http://localhost:4200`
2. Ir em **Funcionárias** → adicionar pelo menos 2 funcionárias
3. Voltar à grade principal → mês atual deve exibir as funcionárias nas linhas
4. Clicar em uma célula de dia útil → digitar um número → pressionar Enter ou Tab
5. Verificar que a célula salva e o total do dia atualiza
6. Clicar em outra célula → pressionar botão de falta → selecionar motivo → confirmar
7. Verificar que a célula exibe "FALTA" e não entra no total
8. Clicar em **Exportar Excel** → abrir o `.xlsx` gerado

---

## 4. Critérios de aceite validados localmente

- [ ] Grade exibe todos os dias do mês (colunas) × funcionárias ativas (linhas)
- [ ] Célula salva ao sair (`blur`) sem botão explícito
- [ ] Falta abre diálogo de motivo antes de salvar
- [ ] Totais por dia, semana e mês atualizam automaticamente após save
- [ ] Excel exportado abre no LibreOffice/Excel com duas abas (Produção, Faltas)
- [ ] Falha de rede exibe toast de erro e restaura valor anterior na célula
- [ ] Mês anterior pode ser aberto e editado via seletor mês/ano

---

## 5. Publicação em rede local

```bash
# Publicar Angular dentro do backend para servir como arquivo estático
cd frontend && ng build --configuration production
cp -r dist/frontend/* ../backend/EstoqueIncenso.Api/wwwroot/

cd ../backend/EstoqueIncenso.Api
dotnet publish -c Release -o publish/

# Rodar na máquina que será o servidor:
dotnet publish/EstoqueIncenso.Api.dll --urls "http://0.0.0.0:5000"
```

Acessar de qualquer máquina na rede: `http://IP_DO_SERVIDOR:5000`
