# Quickstart: validating feature 003

## Prerequisites
Docker Desktop running; Python 3.11 and `uv`; an LLM: a local Ollama (`ollama serve` with `qwen2.5:14b`
pulled) or a Claude key. Nothing else (no embeddings).

## Run

```bash
cd /Users/gabrielmnoma/Coding/tests/project-R
docker compose up -d db
set -a && source .env && set +a
uv run python -m pedido      # http://127.0.0.1:8000
```

`.env` for the local Ollama: `DATABASE_URL`, `LLM_PROVIDER=openai_compatible`,
`LLM_BASE_URL=http://localhost:11434/v1`, `LLM_MODEL=qwen2.5:14b`, `LLM_API_KEY=ollama`.

## Automated validation (no internet)

```bash
uv run pytest
```

## Manual scenarios (chat page)

| # | Send | Expect |
|---|---|---|
| 1 | `2 dz abre caminho, meia dúzia de arruda, 3 dz sao jorge, 1 dz são jorge` | the list in Excel order: Abre Caminho — 2 dz, Arruda — 0,5 dz, São Jorge — 4 dz, then `ok ou não?` |
| 2 | `1 dz abre camino` | `Abre Caminho — 1 dz`, no remark |
| 3 | `1 dz santa defesa santa paz e protecao` and `1 dz sete linhas` | `S. Def.S.Paz e Proteção` and `7 Linhas` |
| 4 | `ok` | `Pedido confirmado. Segue a planilha.` and a download link; open it in Excel |
| 5 | an order, then `não` | `Pedido cancelado. Pode enviar o pedido novamente.` |
| 6 | an order, then another order, then `ok` | the file has only the second order |
| 7 | `ok` with nothing pending | `Envie o seu pedido para eu montar a lista.`, no file |
| 8 | an order, restart the app (`Ctrl+C`, run again), `ok` | the Excel is sent |
| 9 | stop Ollama, send an order | `Não consegui ler o pedido agora. Envie de novo em instantes.` |
| 10 | start without `DATABASE_URL` | refusal in Portuguese, exit code 1 |

## Done when
All tests pass, scenarios 1–10 behave as listed, and the regression run reaches the intended product
for at least 90% of the lines.
