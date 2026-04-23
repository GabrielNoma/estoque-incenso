# Spec — Calendário Compacto com Data Inicial Hoje

## Visão geral

Melhoria na experiência de navegação por mês e data no sistema de controle de produção. O seletor de mês/data deve ocupar menos espaço visual na interface e, ao carregar o sistema, deve exibir automaticamente o mês e dia correntes — eliminando a necessidade de navegação manual para chegar à data de hoje.

---

## Usuários

- **Gestor:** único usuário. Acessa o sistema diariamente para registrar produção. Espera que o sistema abra sempre no contexto do dia atual sem etapas extras.

---

## Funcionalidades

### 1. Compactação visual do calendário/seletor de mês

- O componente de seleção de mês/data deve ocupar menos espaço vertical e horizontal na tela.
- Controles de navegação (anterior/próximo mês, seletor de ano) devem ser agrupados de forma mais densa, reduzindo margens e tamanhos internos.
- A leitura das informações do mês/data selecionados deve permanecer clara e legível após a compactação.
- Nenhuma funcionalidade existente (navegação para meses anteriores, edição de registros históricos) deve ser removida.

### 2. Data inicial ao carregar o sistema

- Ao abrir o sistema pela primeira vez em uma sessão, o calendário/seletor de mês deve posicionar automaticamente no **mês e ano atuais**.
- O cursor ou destaque de dia deve indicar o **dia de hoje** dentro do mês corrente.
- Não é necessária nenhuma ação do gestor para chegar à data de hoje — o sistema deve chegar lá por conta própria.

---

## Regras de negócio

- "Hoje" é determinado pela data do dispositivo/navegador do gestor no momento do carregamento.
- Se o gestor navegar para outro mês durante a sessão e recarregar a página, o sistema deve voltar para hoje (não memorizar a última posição navegada).
- A compactação não deve esconder ou remover controles existentes de navegação por mês/ano.

---

## Cenários de usuário e testes

### Cenário 1 — Abertura do sistema no dia atual
**Dado** que o gestor abre o sistema  
**Quando** a página carrega  
**Então** o calendário exibe o mês e ano atuais automaticamente  
**E** o dia de hoje está visualmente destacado ou selecionado  

### Cenário 2 — Compactação preserva navegação
**Dado** que o gestor está com o calendário compacto carregado  
**Quando** ele clica para navegar para o mês anterior  
**Então** o calendário muda para o mês anterior normalmente  
**E** todos os controles de navegação continuam funcionais  

### Cenário 3 — Recarga da página após navegação
**Dado** que o gestor navegou para um mês passado  
**Quando** ele recarrega a página  
**Então** o calendário volta para o mês/dia atual automaticamente  

### Cenário 4 — Leitura clara após compactação
**Dado** que o calendário foi compactado  
**Quando** o gestor visualiza o seletor  
**Então** os nomes dos dias, números e controles ainda são legíveis sem zoom  

---

## Requisitos funcionais

| ID   | Requisito |
|------|-----------|
| RF01 | Ao carregar, o sistema posiciona automaticamente o calendário no mês e ano do dia atual |
| RF02 | O dia de hoje é destacado visualmente no calendário ao carregar |
| RF03 | O componente de calendário/seletor ocupa menor área visual que o atual (altura e/ou largura reduzidas) |
| RF04 | Todos os controles de navegação por mês e ano permanecem presentes e funcionais após compactação |
| RF05 | A recarga da página sempre retorna ao mês/dia atual, independentemente da navegação anterior |

---

## Critérios de sucesso

- O gestor não precisa clicar em nenhum botão para chegar ao dia/mês atual após abrir o sistema
- O calendário ocupa visivelmente menos espaço na tela em comparação com o estado anterior
- Nenhum controle de navegação existente é removido ou fica inacessível
- O gestor consegue ler todos os elementos do calendário sem dificuldade após a compactação

---

## Fora do escopo

- Memorização da última posição navegada entre sessões
- Configuração de tamanho do calendário pelo gestor
- Mudança no formato de exibição de data (dia/mês/ano)
- Qualquer alteração nas funcionalidades de registro de produção ou faltas

---

## Premissas

- "Calendário" refere-se ao seletor de mês/data já existente na tela principal de produção
- O dispositivo do gestor tem a data/hora correta configurada
- A compactação visual será perceptível para o gestor sem prejudicar a usabilidade
