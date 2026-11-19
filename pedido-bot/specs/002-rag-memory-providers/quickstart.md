# Quickstart: validating feature 002

A run/validation guide. Details live in [data-model.md](data-model.md) and the files under
[contracts/](contracts/).

## Prerequisites

1. **Docker Desktop running** (the database and all database tests need it).
2. Python 3.11 and `uv` (as in 001).
3. A configured language model (Claude key, or an OpenAI-compatible service) and, for the memory, an
   embeddings service. Without the embeddings variables the tool works as in 001.

## Setup and run

```bash
cd /Users/gabrielmnoma/Coding/tests/project-R
cp .env.example .env            # then fill in the keys; never commit secrets
docker compose up -d db         # Postgres + pgvector on localhost:5433
set -a && source .env && set +a
uv sync
uv run python -m pedido         # applies the schema, then serves http://127.0.0.1:8000
```

## Automated validation (no internet)

```bash
uv run pytest tests/unit tests/contract tests/integration
```

Expected: all pass, including the 001 tests (migrated to the new database), the fake OpenAI-compatible
server tests, the look-alike guard tests and the SC-004 measurement. If Postgres is not running the
database tests **fail with the instruction** `docker compose up -d db`.

## Manual scenarios

| # | Do this | Expect |
|---|---|---|
| 1 | Start without `DATABASE_URL` | does not start; Portuguese message; exit code 1 |
| 2 | Start with `DATABASE_URL` pointing to a stopped Postgres | does not start; Portuguese message about the connection |
| 3 | Approve an order, restart the tool, open the history | order still there; download works |
| 4 | Approve an order with the embeddings configured | history shows **Memorizado** |
| 5 | Stop the embeddings service (or point `EMBED_BASE_URL` at an address that does not answer), approve an order | approval succeeds; history shows **Memória pendente** |
| 6 | Set the key again, run `uv run python -m pedido.reprocess` | prints the counts; the order shows **Memorizado**; running it again changes nothing |
| 7 | Confirm "abre c felicidade" → Abre C. da Felicidade; later paste a close variant ("abre c felicidad") | line flagged **Revisar** with the product pre-selected and the reason "parecido com um pedido anterior"; Aprovar stays blocked until you confirm |
| 8 | With "abre caminho" remembered, paste "abre caminho da felicidade" | never pre-selected as "Abre Caminho"; candidates include "Abre C. da Felicidade" |
| 9 | Switch `LLM_PROVIDER` between `anthropic` and `openai_compatible` and run `scripts/run_regression_real.py --real` | both complete the regression messages with no code change |
| 10 | Search the history, API responses and `pedido` tables for the key text | 0 occurrences |

## Done when

All automated tests pass; scenarios 1–10 behave as listed; the regression run meets SC-002 and SC-004
of the spec; and `specs/001` acceptance scenarios still pass unchanged (SC-008).
