# Contrato da API do bot de pedidos

Para quem consome a API: o sistema de estoque e, depois, o adaptador do WhatsApp. Todos os erros são JSON em
português: `{"erro": "<código>", "mensagem": "<texto>"}`.

## Chave de acesso

Toda rota, exceto `GET /saude`, exige uma chave, em um destes cabeçalhos (se os dois vierem, vale o
`Authorization`):

```text
Authorization: Bearer <chave>
X-API-Key: <chave>
```

As chaves ficam **só** na variável de ambiente `API_KEYS` do bot, no formato
`nome:escopos:chave`, separadas por vírgula, com escopos unidos por `+` e chaves de pelo menos 32 caracteres:

```text
API_KEYS=estoque:conversa+modelo:<CHAVE1>,whatsapp:conversa:<CHAVE2>
```

| Escopo | Dá acesso a |
|---|---|
| `conversa` | enviar mensagens e baixar a planilha de um pedido confirmado |
| `modelo` | exportar, importar e consultar o modelo da planilha |

Gerar uma chave: `python3 -c "import secrets; print(secrets.token_urlsafe(32))"`. Nunca coloque a chave em
código, em repositório ou em log.

## Rotas

| Rota | Escopo | O que faz |
|---|---|---|
| `GET /saude` | nenhum (pública) | `200 {"status":"ok"}` ou `503 {"status":"indisponivel"}`, sem mais nada |
| `POST /api/mensagem` | `conversa` | recebe `{"telefone","texto"}` e devolve `{"resposta","arquivo"}` |
| `GET /api/pedidos/{pedido_id}/planilha` | `conversa` | baixa o `.xlsx` de um pedido confirmado |
| `GET /api/modelo` | `modelo` | baixa o modelo ativo (`modelo-pedido.xlsx`) |
| `POST /api/modelo` | `modelo` | importa um novo modelo (corpo = bytes do `.xlsx`) |
| `GET /api/modelo/info` | `modelo` | versão, arquivo, produtos e data do modelo ativo |

Em produção (`ENVIRONMENT=producao`) a página de teste, `/static`, `/docs`, `/redoc` e `/openapi.json` não
existem (404).

## Exemplos

```bash
# saúde (sem chave)
curl -s https://SEU-BOT/saude

# mandar uma mensagem
curl -s -X POST https://SEU-BOT/api/mensagem \
  -H "Authorization: Bearer $CHAVE" -H "Content-Type: application/json" \
  -d '{"telefone": "estoque-web-123", "texto": "2 dz abre caminho e meia duzia de arruda"}'

# baixar a planilha de um pedido confirmado
curl -s -o pedido-12.xlsx -H "X-API-Key: $CHAVE" https://SEU-BOT/api/pedidos/12/planilha

# exportar o modelo
curl -s -o modelo-pedido.xlsx -H "Authorization: Bearer $CHAVE" https://SEU-BOT/api/modelo

# importar um novo modelo
curl -s -X POST --data-binary @modelo-novo.xlsx -H "Content-Type: application/octet-stream" \
  -H "X-Nome-Arquivo: modelo-novo.xlsx" -H "Authorization: Bearer $CHAVE" https://SEU-BOT/api/modelo

# informação do modelo ativo
curl -s -H "Authorization: Bearer $CHAVE" https://SEU-BOT/api/modelo/info
```

## Erros

| Status | `erro` | Quando |
|---|---|---|
| 401 | `chave_ausente` | nenhuma chave enviada |
| 401 | `chave_invalida` | chave desconhecida |
| 403 | `sem_permissao` | a chave não tem o escopo da rota |
| 413 | `corpo_grande` | o corpo de uma mensagem passa de `MAX_CORPO_MENSAGEM_KB` (padrão 64 KB) |
| 413 | `modelo_grande` | o modelo importado passa de `MAX_MODELO_MB` (padrão 5 MB) |
| 422 | `modelo_invalido` | o arquivo importado não serve como modelo (a mensagem diz o que conferir) |
| 422 | `requisicao_invalida` | campos ausentes ou de tipo errado |
| 404 | `pedido_nao_encontrado` | pedido inexistente |
| 409 | `pedido_nao_confirmado` | o pedido ainda não foi confirmado com `ok` |
| 429 | `muitas_requisicoes` | a chave passou do limite por minuto (`LIMITE_REQ_POR_CHAVE`, padrão 120) |

Respostas de conversa (`resposta` de `POST /api/mensagem`) para limites são frases curtas e neutras: o limite
de mensagens do dia por conversa (`LIMITE_DIARIO_CONVERSA`, padrão 200), muitas mensagens seguidas, mensagem
longa demais, quantidade acima de 1000 dz de um produto e o serviço ocupado.

## Identificador da conversa

O campo `telefone` aceita qualquer texto estável: o número do cliente (WhatsApp) ou um identificador anônimo
por navegador (tela do estoque). O pedido pendente, o limite diário e a memória são por esse identificador.

## Observações

- A primeira resposta de uma mensagem leva alguns segundos (leitura do pedido pelo modelo de linguagem);
  configure no cliente um tempo de espera de pelo menos 60 s.
- Quem tem a chave com escopo `modelo` pode substituir o modelo para todos. Os modelos antigos ficam
  guardados no banco.
