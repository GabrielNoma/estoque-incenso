# Contract: new neutral replies (pt-BR, constants of `messages.py`)

| Constant | Text | When |
|---|---|---|
| `MENSAGEM_LONGA` | "Mensagem muito longa. Envie o pedido em partes menores." | order text above `MAX_MENSAGEM`; the model is not called; pending order kept |
| `MUITAS_MENSAGENS` | "Muitas mensagens seguidas. Aguarde um instante e envie de novo." | rate limit exceeded; message ignored |
| `QUANTIDADE_ALTA` | "Quantidade acima do limite. Envie o pedido novamente com uma quantidade menor." | one product above `MAX_QTD_PRODUTO` dozens; no list; nothing pending created; previous pending kept |

Startup/script texts (also constants): `ERRO_VECTOR_INDISPONIVEL`, `ERRO_DIMENSAO_DIFERENTE`,
`APELIDO_NAO_ENCONTRADO`, and the column headers of the script. Nothing in any reply mentions the memory.
Replies of 003 are unchanged.
