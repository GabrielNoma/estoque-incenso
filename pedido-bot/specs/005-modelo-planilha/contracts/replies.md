# Contract: new texts (pt-BR, constants of `messages.py`)

Replies to the customer:

| Constant | Text | When |
|---|---|---|
| `MODELO_INVALIDO` | "Não consegui usar a planilha modelo. Confira o modelo e tente de novo." | an order arrives and the active model cannot be read or has no products |
| `MODELO_PRODUTO_AUSENTE` | "Um produto do pedido não está mais na planilha modelo. Confira o modelo e envie o pedido novamente." | ok, and a product of the pending order is missing from the active model; no file; order stays pending |

API messages for `422 modelo_invalido` (each ends by asking to check the model):

| Constant | Text |
|---|---|
| `MODELO_VAZIO` | "O arquivo está vazio. Confira o modelo e envie de novo." |
| `MODELO_XLS` | "Esse arquivo é do formato antigo (.xls). Salve o modelo como .xlsx e envie de novo." |
| `MODELO_ILEGIVEL` | "Não consegui ler o arquivo como planilha .xlsx. Confira o modelo e envie de novo." |
| `MODELO_SEM_PRODUTOS` | "Não encontrei produtos nas colunas esperadas (C, G, K, O e S, linhas 4 a 46). Confira o modelo e envie de novo." |
| `MODELO_NOME_REPETIDO` | "O produto \"{nome}\" aparece mais de uma vez. Confira o modelo e envie de novo." |
| `MODELO_CELULA_MESCLADA` | "A célula de quantidade {celula} está mesclada. Confira o modelo e envie de novo." |
| `MODELO_GRANDE` | "O arquivo é grande demais (limite de {limite} MB). Confira o modelo e envie de novo." |
