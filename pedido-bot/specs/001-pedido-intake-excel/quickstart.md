# Quickstart: validating Pedido a partir de mensagem de WhatsApp

A run/validation guide, not an implementation guide. Details live in [data-model.md](data-model.md)
and [contracts/http-api.md](contracts/http-api.md).

## Prerequisites

1. Python 3.11 and `uv` (both already installed on this machine).
2. **One-time template step (research D1/A2):** open `assets/original/PLANILHA 2024.xls` in Excel →
   *Salvar como* → `.xlsx` → save as `assets/PLANILHA_2024.xlsx`. The original `.xls` stays untouched.
3. `export ANTHROPIC_API_KEY=...` in the shell (never written to a file in the repo).

## Setup and run

> Desde a feature 002 o app precisa do Postgres: veja `specs/002-rag-memory-providers/quickstart.md`.

```bash
cd /Users/gabrielmnoma/Coding/tests/project-R
cp .env.example .env                 # preencha as chaves; nunca versione segredos
docker compose up -d db              # Postgres + pgvector em localhost:5433
set -a && source .env && set +a
uv sync
uv run python -m pedido              # aplica o schema e serve http://127.0.0.1:8000
```

## Automated validation (no network)

```bash
uv run pytest tests/unit tests/contract tests/integration
```

Expected: all pass with the LLM stubbed. Includes the "must never confuse" cases and the template
check (189 formulas preserved, each quantity in its product's row).

## Manual scenarios (end to end, real API)

| # | Do this | Expect |
|---|---|---|
| 1 | Paste `2 dz abre caminho, meia dúzia de arruda, 3 dz sao jorge` → Analisar | table with 3 lines, 0.5 for arruda, totals per category shown |
| 2 | Paste `1 dz abre c. da felicidade` | matches **Abre C. da Felicidade**, never Abre Caminho |
| 3 | Paste `1 dz abre camino` (typo) | line marked **revisar** with up to 3 "Abre …" candidates, nothing chosen silently |
| 4 | Leave a line without product → Aprovar | blocked, line highlighted, pt-BR message |
| 5 | Fix the lines → Aprovar → Baixar planilha | `.xlsx` opens **in Excel** (previews show blank totals until Excel recalculates); each quantity beside the right product; totals correct; header input cells empty |
| 5b | Leave a "revisar" line with a suggested product untouched → Aprovar | blocked until you confirm that line; two lines for one product must be merged first |
| 6 | Paste the same phrase from #3 again after confirming it | matched automatically (no revisar) |
| 7 | Unset `ANTHROPIC_API_KEY`, paste a message | pt-BR error, text kept, empty table to fill by hand |
| 8 | Open history | each line shows suggestion next to final answer |

## Done when

All automated tests pass, scenarios 1–8 behave as listed, and the 20-message regression set meets
the spec's success criteria (≥ 90% lines correct without edits, 0 wrong auto-accepts).
