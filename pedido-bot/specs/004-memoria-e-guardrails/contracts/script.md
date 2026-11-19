# Contract: `scripts/apelidos.py`

```text
uv run python scripts/apelidos.py                 # lists
uv run python scripts/apelidos.py --desativar 12  # status -> desativado
uv run python scripts/apelidos.py --ativar 12     # status -> ativo
```

List columns (Portuguese): `id | texto | produto | positivos | negativos | status | aplica` (`aplica` =
sim/não by the rule of D1). Unknown id: prints `APELIDO_NAO_ENCONTRADO`, exit code 1, changes nothing.
Nothing is ever deleted. Needs `DATABASE_URL`.
