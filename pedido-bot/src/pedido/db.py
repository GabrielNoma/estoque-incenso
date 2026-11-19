"""Postgres access: connections, schema and the startup check.

One connection per operation; no prepared statements, so it also works behind a transaction pooler
(Supabase). `StartupError` carries a Portuguese message and stops the application.
"""
import psycopg

from pedido import config, messages

CONNECT_TIMEOUT_SECONDS = 5


class StartupError(Exception):
    """The application must not start; `str(error)` is the message to show (pt-BR)."""


def connect(url: str) -> psycopg.Connection:
    """Open a connection. Used as `with connect(url) as conn:` it commits on success and closes."""
    return psycopg.connect(url, prepare_threshold=None, connect_timeout=CONNECT_TIMEOUT_SECONDS)


def apply_schema(url: str, dimensions: int | None = None) -> None:
    """Apply every pending migration (used by tests and scratch databases; the app only verifies)."""
    from pedido import migrate

    migrate.aplicar(url, dimensions)


def _stored_dimensions(url: str) -> int | None:
    with connect(url) as conn:
        row = conn.execute(
            "select a.atttypmod from pg_attribute a join pg_class c on c.oid = a.attrelid "
            "join pg_namespace n on n.oid = c.relnamespace "
            "where n.nspname = 'pedido' and c.relname = 'apelidos' and a.attname = 'embedding'").fetchone()
    return row[0] if row and row[0] > 0 else None


def check_database(url: str | None, dimensions: int | None = None) -> None:
    """Make sure the database is ready; raise StartupError (pt-BR) otherwise.

    Migrations are only VERIFIED (pending or altered ones refuse the start); they are applied by
    `python -m pedido.migrate`, or here only when MIGRATE_ON_START=true (a local convenience).
    """
    from pedido import migrate

    if not url:
        raise StartupError(messages.ERRO_BANCO_NAO_CONFIGURADO)
    size = dimensions or config.embed_dimensions()
    try:
        if config.migrate_on_start():
            migrate.aplicar(url, size)
        migrate.verificar(url)
        stored = _stored_dimensions(url)
    except psycopg.Error as error:
        raise StartupError(messages.ERRO_BANCO_INACESSIVEL) from error
    if stored is not None and stored != size:
        raise StartupError(messages.ERRO_DIMENSAO_DIFERENTE.format(guardado=stored, configurado=size))
