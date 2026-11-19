# Quickstart: validating feature 005

Prerequisites: as 004 (`docker compose up -d db`, `ollama serve`, `.env`), the app running.

1. `uv run pytest` → all green.
2. **Export**: `curl -o modelo.xlsx localhost:8000/api/modelo` → open it in Excel: the form with its formulas.
3. **Edit**: in a free row of a block, write a new product name (for example `Incenso Teste`), save as `.xlsx`.
4. **Import**: `curl -X POST --data-binary @modelo.xlsx -H 'X-Nome-Arquivo: modelo.xlsx' localhost:8000/api/modelo`
   → JSON with `adicionados: ["Incenso Teste"]`, `versao: 2`.
5. **Use it**: in the chat send `2 dz incenso teste`, answer `ok`, open the Excel: the quantity is beside the new
   product. No restart was needed.
6. **Refuse**: import a `.xls`, an empty file and a copy with a repeated name: each returns one Portuguese
   message; `GET /api/modelo/info` still shows version 2.
7. **Model problem**: make an order, import a model without one of its products, answer `ok`: the reply asks to
   check the model and the order stays pending.
8. **Nicknames**: `uv run python scripts/apelidos.py` shows nicknames of removed or renamed products disabled.
