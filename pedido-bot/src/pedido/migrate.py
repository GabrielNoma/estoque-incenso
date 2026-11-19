"""Versioned migrations (Constitution VI; research D5).

Ordered files in `migrations/`, each applied in its own transaction and recorded with its version and the
SHA-256 of the raw file in `pedido.schema_migrations`. The application only VERIFIES (see `db.check_database`);
applying is this separate command: `python -m pedido.migrate` (and `--status` to look without changing).
"""
import hashlib
import os
import sys
from dataclasses import dataclass
from pathlib import Path

import psycopg

from pedido import config, messages
from pedido.db import StartupError, connect

MIGRATIONS_DIR = Path(__file__).with_name("migrations")
LOCK_ID = 5006


@dataclass(frozen=True)
class Migracao:
    versao: str
    arquivo: str
    checksum: str
    sql: str


def arquivos() -> list[Migracao]:
    """The migration files, in name order."""
    result = []
    for caminho in sorted(MIGRATIONS_DIR.glob("*.sql")):
        raw = caminho.read_bytes()
        result.append(Migracao(caminho.name.split("_", 1)[0], caminho.name,
                               hashlib.sha256(raw).hexdigest(), raw.decode("utf-8")))
    return result


def _registradas(url: str) -> dict[str, str]:
    """{version: checksum} already applied; empty when the table does not exist (nothing is created here)."""
    with connect(url) as conn:
        if conn.execute("select to_regclass('pedido.schema_migrations')").fetchone()[0] is None:
            return {}
        return dict(conn.execute("select versao, checksum from pedido.schema_migrations").fetchall())


def status(url: str) -> list[dict]:
    aplicadas = _registradas(url)
    result = []
    for m in arquivos():
        if m.versao not in aplicadas:
            estado = "pendente"
        else:
            estado = "aplicada" if aplicadas[m.versao] == m.checksum else "alterada"
        result.append({"versao": m.versao, "arquivo": m.arquivo, "estado": estado})
    return result


def verificar(url: str) -> None:
    """Raise a Portuguese `StartupError` when a migration is altered or still pending."""
    estados = status(url)
    for item in estados:
        if item["estado"] == "alterada":
            raise StartupError(messages.ERRO_MIGRACAO_ALTERADA.format(arquivo=item["arquivo"]))
    pendentes = [i["arquivo"] for i in estados if i["estado"] == "pendente"]
    if pendentes:
        raise StartupError(messages.ERRO_MIGRACOES_PENDENTES.format(lista=", ".join(pendentes)))


def aplicar(url: str, dimensions: int | None = None) -> list[str]:
    """Apply the pending migrations in order, each in its own transaction. Returns the files applied."""
    tamanho = str(int(dimensions or config.embed_dimensions()))
    try:
        with connect(url) as conn:
            conn.execute("create schema if not exists pedido; create table if not exists pedido.schema_migrations ("
                         "versao text primary key, arquivo text not null, checksum text not null, "
                         "aplicada_em timestamptz not null default now());"
                         "alter table pedido.schema_migrations enable row level security")
    except psycopg.Error as error:
        raise StartupError(messages.ERRO_BANCO_INACESSIVEL) from error
    feitas = []
    for m in arquivos():
        aplicadas = _registradas(url)
        if m.versao in aplicadas:
            continue  # an altered file is reported by `verificar`; it is never re-run or overwritten
        try:
            with connect(url) as conn:
                conn.execute("select pg_advisory_xact_lock(%s)", (LOCK_ID,))
                conn.execute(m.sql.replace("__DIMENSIONS__", tamanho))
                conn.execute("insert into pedido.schema_migrations (versao, arquivo, checksum) values (%s, %s, %s)",
                             (m.versao, m.arquivo, m.checksum))
        except (psycopg.errors.UndefinedFile, psycopg.errors.FeatureNotSupported) as error:
            raise StartupError(messages.ERRO_VECTOR_INDISPONIVEL) from error
        except psycopg.Error as error:
            raise StartupError(messages.ERRO_MIGRACAO_FALHOU.format(arquivo=m.arquivo)) from error
        feitas.append(m.arquivo)
    return feitas


def main(argv: list[str] | None = None) -> int:
    args = list(sys.argv[1:] if argv is None else argv)
    url = os.environ.get("DATABASE_URL")
    if not url:
        print(messages.ERRO_BANCO_NAO_CONFIGURADO, file=sys.stderr)
        return 1
    try:
        if "--status" in args:
            for item in status(url):
                print(f"{item['versao']} | {item['arquivo']} | {messages.MIGRACAO_ESTADOS[item['estado']]}")
            return 0
        feitas = aplicar(url)
    except StartupError as error:
        print(str(error), file=sys.stderr)
        return 1
    for arquivo in feitas:
        print(messages.MIGRACAO_APLICADA.format(arquivo=arquivo))
    if not feitas:
        print(messages.MIGRACAO_NADA)
    return 0


if __name__ == "__main__":
    sys.exit(main())
