# Contract: the bot's replies (exact texts, pt-BR)

All texts live in `src/pedido/messages.py`; tests compare against those constants.

| Situation | Reply |
|---|---|
| An order was read | `<Produto> — <quantidade> dz` per line (Excel order), a blank line, `ok ou não?` |
| ok, file generated | `Pedido confirmado. Segue a planilha.` (+ the file) |
| não | `Pedido cancelado. Pode enviar o pedido novamente.` |
| ok / não with nothing pending | `Envie o seu pedido para eu montar a lista.` |
| message with no items (or empty) | `Não encontrei itens nessa mensagem. Envie o pedido novamente.` |
| the model failed or is not configured | `Não consegui ler o pedido agora. Envie de novo em instantes.` |
| the file could not be generated | `Não consegui gerar a planilha agora. Responda ok de novo em instantes.` |
| the database failed | `Não consegui registrar agora. Envie de novo em instantes.` |

Format of a line: the product's official name, an em dash with spaces, the quantity in dozens with a
comma for decimals and no trailing zeros (`2`, `0,5`, `2,25`), the word `dz`.
Accepted ok words, no words and the rule "anything else is an order": see research D3.
