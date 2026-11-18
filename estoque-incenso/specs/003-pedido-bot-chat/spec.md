# Spec — Tela "Pedidos" (conversa com o robô de pedidos)

**Feature**: 003-pedido-bot-chat

## Visão geral

Nova tela "Pedidos" no sistema de estoque, aberta a qualquer pessoa (o sistema não tem login). A pessoa digita um pedido em texto livre, o robô de pedidos responde com a lista organizada terminando em "ok ou não?", a pessoa responde "ok" e recebe a planilha Excel do pedido para baixar. A mesma tela permite exportar o modelo atual da planilha de pedido e importar um novo modelo (por exemplo, para incluir produtos novos).

## Cenários de usuário

### US1 — Fazer um pedido pelo chat (P1)
Como qualquer pessoa, quero escrever o pedido em texto livre e conversar com o robô até confirmar, para receber a planilha pronta.
- Dado que abri a tela, quando envio "2 dz abre caminho e meia duzia de arruda", então vejo minha mensagem à direita, um indicador "digitando..." e, depois, a resposta do robô à esquerda com a lista organizada (quebras de linha preservadas) terminando em "ok ou não?".
- Quando respondo "ok", então a resposta do robô traz o link "Baixar planilha" que baixa o Excel do pedido confirmado.
- Enquanto aguardo a resposta, a caixa de mensagem e o botão Enviar ficam desabilitados.
- Enter envia; a conversa rola até a última mensagem.
- Se o robô responder que um produto não está no modelo (pedindo para conferir o modelo), a frase aparece como balão normal.
- Cada navegador tem sua própria conversa/pedido pendente (identificador anônimo guardado no navegador).

### US2 — Exportar o modelo atual (P2)
Quero baixar a planilha-modelo que o robô preenche, para editá-la.
- Ao clicar em "Exportar modelo", o arquivo `modelo-pedido.xlsx` é baixado.

### US3 — Importar um novo modelo (P2)
Quero enviar um modelo editado para o robô passar a usá-lo.
- Ao escolher um arquivo .xlsx em "Importar modelo", um diálogo de confirmação avisa que o novo modelo substitui o ativo para todos e que os modelos anteriores são mantidos.
- Confirmando, o arquivo é enviado; em caso de sucesso vejo um resumo: versão, número de produtos, produtos adicionados, removidos e renomeados.
- Se o modelo for inválido (ou grande demais), vejo exatamente a mensagem em português do robô (que diz para conferir o modelo); o modelo ativo não muda.
- Uma linha informativa mostra o modelo ativo (versão, arquivo, número de produtos), atualizada após importar.

## Requisitos funcionais

- FR-001 A tela "Pedidos" é acessível por item "Pedidos" no menu lateral e pela rota `/pedidos`, sem login.
- FR-002 Mensagens da pessoa são enviadas ao robô e as respostas exibidas como balões (pessoa à direita, robô à esquerda).
- FR-003 Mostrar "digitando..." e desabilitar a entrada enquanto aguarda (a resposta pode levar de 5 a 20 segundos).
- FR-004 Quando a resposta tem arquivo, exibir "Baixar planilha".
- FR-005 Cada navegador mantém um identificador anônimo de conversa persistente.
- FR-006 "Exportar modelo" baixa o modelo ativo.
- FR-007 "Importar modelo" exige confirmação e envia o arquivo com o nome original; mostra resumo em sucesso e a mensagem do robô em erro 422/413.
- FR-008 Exibir informações do modelo ativo.
- FR-009 Se o serviço de pedidos estiver indisponível ou demorar demais, exibir "O serviço de pedidos não está disponível. Tente novamente em instantes."
- FR-010 Todos os textos em português do Brasil; tela acessível por teclado e leitores de tela.
- FR-011 O servidor do estoque não registra em log o texto dos pedidos nem os identificadores de conversa (Constituição III com privacidade).

## Critérios de sucesso

- SC-001 Uma pessoa sem treinamento consegue ir do texto do pedido ao Excel baixado em menos de 2 minutos.
- SC-002 100% das mensagens de erro do robô sobre modelo inválido aparecem na tela sem alteração.
- SC-003 Importar um modelo válido mostra o resumo de mudanças em até 5 segundos após a resposta do robô.

## Premissas

- O robô de pedidos é um serviço separado já em execução; o estoque apenas o consome por HTTP e o endereço é configurável (`PEDIDO_BOT_URL`, padrão `http://127.0.0.1:8000`).
- O navegador nunca fala direto com o robô; o backend do estoque faz o intermédio.
- Fora do escopo: login, histórico de conversas no servidor, edição do modelo dentro do sistema.

## Entidades

- Conversa (identificador anônimo por navegador), Mensagem (autor, texto, arquivo opcional), Modelo de pedido (versão, arquivo, produtos).
