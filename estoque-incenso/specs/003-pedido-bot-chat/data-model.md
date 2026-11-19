# Modelo de dados
Sem persistência no estoque. Tipos trafegados:
- MensagemChat: `{ autor: 'pessoa'|'robo', texto, arquivo?: { nome, url } }`
- RespostaBot: `{ resposta, arquivo: null | { nome, url } }`
- InfoModelo: `{ versao, arquivo, produtos, ativado_em }`
- ResultadoImportacao: `{ versao, arquivo, produtos, adicionados[], removidos[], renomeados[{de,para}], apelidos_desativados }`
- ErroBot: `{ erro, mensagem }`
