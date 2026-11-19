# Contract: memory reprocess command

```bash
uv run python -m pedido.reprocess [--batch N] [--dry-run]
```

Completes memory that is pending or was made with another embedding model. Run it after an embeddings
outage or after changing `EMBED_MODEL`.

## Behavior

1. Validates configuration like startup (database; embedder fully configured). Otherwise prints the
   Portuguese message from `contracts/configuration.md` and exits with `1`.
2. **Backfill**: approved runs whose `memoria_estado` is `nao_aplicavel` (approved while the embeddings
   were not configured) get their memory rows created from their final approved lines, so no learning
   data is lost.
3. Selects `memoria_linhas` and `memoria_mensagens` rows with `embedding IS NULL` **or**
   `modelo_embedding` different from `EMBED_MODEL`.
4. Embeds them in batches (`--batch`, default 50), updates `embedding` and `modelo_embedding`; if an
   update would collide with the unique key, the older duplicate row is dropped.
5. Sets `runs.memoria_estado = 'completa'` for every run whose memory rows are all complete.
6. `--dry-run` only reports the counts.

## Properties

- **Idempotent**: running it twice changes nothing the second time; no duplicates are created.
- **Interruptible**: batches are committed one by one; running it again finishes the rest.
- Never prints keys or message text.

## Output (pt-BR) and exit codes

```text
Linhas pendentes: 12 · Mensagens pendentes: 3
Concluído: 12 linhas e 3 mensagens atualizadas. Nenhuma memória pendente.
```

| Exit code | Meaning |
|---|---|
| 0 | nothing left pending |
| 1 | configuration or database error (message printed) |
| 2 | the embeddings service kept failing; some rows are still pending (the count is printed) |
