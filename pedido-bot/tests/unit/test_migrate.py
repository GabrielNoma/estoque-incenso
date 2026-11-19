"""Versioned migrations (Constitution VI): ordered files, one transaction each, version and checksum recorded."""
import hashlib

import pytest

from pedido import db, messages, migrate

REAL = ["0001_baseline.sql", "0002_uso_diario.sql"]


def tables(url):
    with db.connect(url) as conn:
        return {r[0] for r in conn.execute("select table_name from information_schema.tables "
                                           "where table_schema = 'pedido'").fetchall()}


def recorded(url):
    with db.connect(url) as conn:
        return conn.execute("select versao, arquivo, checksum, aplicada_em from pedido.schema_migrations "
                            "order by versao").fetchall()


@pytest.fixture
def pasta(tmp_path, monkeypatch):
    """A throwaway migrations folder in place of the real one."""
    monkeypatch.setattr(migrate, "MIGRATIONS_DIR", tmp_path)
    return tmp_path


def test_apply_on_an_empty_database_applies_every_migration_in_order(scratch_database_url):
    url = scratch_database_url()
    assert migrate.aplicar(url, 1024) == REAL
    assert {"catalog", "pedidos", "apelidos", "modelos", "uso_diario", "schema_migrations"} <= tables(url)
    rows = recorded(url)
    assert [(r[0], r[1]) for r in rows] == [("0001", REAL[0]), ("0002", REAL[1])]
    for row in rows:
        raw = (migrate.MIGRATIONS_DIR / row[1]).read_bytes()
        assert row[2] == hashlib.sha256(raw).hexdigest()


def test_applying_twice_changes_nothing(scratch_database_url):
    url = scratch_database_url()
    migrate.aplicar(url, 1024)
    before = recorded(url)
    assert migrate.aplicar(url, 1024) == []
    assert recorded(url) == before


def test_status_lists_each_migration_and_changes_nothing(scratch_database_url):
    url = scratch_database_url()
    assert [(s["arquivo"], s["estado"]) for s in migrate.status(url)] == [(f, "pendente") for f in REAL]
    assert "schema_migrations" not in tables(url)  # asking created nothing
    migrate.aplicar(url, 1024)
    assert [s["estado"] for s in migrate.status(url)] == ["aplicada", "aplicada"]


def test_migrations_run_in_file_order_each_in_its_own_transaction(pasta, scratch_database_url):
    (pasta / "0002_segunda.sql").write_text("create table pedido.t2 (id int);", encoding="utf-8")
    (pasta / "0001_primeira.sql").write_text("create table pedido.t1 (id int);", encoding="utf-8")
    (pasta / "0003_ruim.sql").write_text("create table pedido.t3 (id int); select 1 / 0;", encoding="utf-8")
    url = scratch_database_url()
    with pytest.raises(db.StartupError) as error:
        migrate.aplicar(url, 1024)
    assert str(error.value) == messages.ERRO_MIGRACAO_FALHOU.format(arquivo="0003_ruim.sql")
    assert {"t1", "t2"} <= tables(url) and "t3" not in tables(url)  # the failing one was rolled back
    assert [r[0] for r in recorded(url)] == ["0001", "0002"]  # and was not recorded


def test_a_changed_applied_file_is_reported_and_refused(pasta, scratch_database_url):
    arquivo = pasta / "0001_a.sql"
    arquivo.write_text("create table pedido.a (id int);", encoding="utf-8")
    url = scratch_database_url()
    migrate.aplicar(url, 1024)
    arquivo.write_text("create table pedido.a (id int, extra int);", encoding="utf-8")
    assert [s["estado"] for s in migrate.status(url)] == ["alterada"]
    with pytest.raises(db.StartupError) as error:
        migrate.verificar(url)
    assert str(error.value) == messages.ERRO_MIGRACAO_ALTERADA.format(arquivo="0001_a.sql")
    assert migrate.aplicar(url, 1024) == []  # applying never re-runs or overwrites an applied one


def test_verify_refuses_pending_migrations_in_portuguese(pasta, scratch_database_url):
    (pasta / "0001_a.sql").write_text("select 1;", encoding="utf-8")
    url = scratch_database_url()
    with pytest.raises(db.StartupError) as error:
        migrate.verificar(url)
    assert str(error.value) == messages.ERRO_MIGRACOES_PENDENTES.format(lista="0001_a.sql")
    migrate.aplicar(url, 1024)
    migrate.verificar(url)  # now fine


def test_the_baseline_adopts_a_database_that_already_has_the_005_schema(scratch_database_url):
    url = scratch_database_url()
    sql = (migrate.MIGRATIONS_DIR / REAL[0]).read_text(encoding="utf-8").replace("__DIMENSIONS__", "1024")
    with db.connect(url) as conn:  # the database as feature 005 left it (no migration table)
        conn.execute(sql)
        conn.execute("insert into pedido.pedidos (telefone, mensagem, itens, lista) values ('1', 'm', '[]', 'l');"
                     "insert into pedido.modelos (versao, arquivo, conteudo, produtos, ativo) "
                     "values (1, 'a.xlsx', 'x', 1, true);"
                     "insert into pedido.apelidos (texto_normalizado, produto_id, positivos) values ('a', 1, 2)")
    migrate.aplicar(url, 1024)
    with db.connect(url) as conn:
        assert conn.execute("select count(*) from pedido.pedidos").fetchone()[0] == 1
        assert conn.execute("select count(*) from pedido.modelos").fetchone()[0] == 1
        assert conn.execute("select positivos from pedido.apelidos").fetchone()[0] == 2
    assert [r[0] for r in recorded(url)] == ["0001", "0002"] and "uso_diario" in tables(url)


def test_the_vector_size_of_the_baseline_comes_from_the_argument(scratch_database_url):
    url = scratch_database_url()
    migrate.aplicar(url, 768)
    with pytest.raises(db.StartupError) as error:
        db.check_database(url, 1024)
    assert str(error.value) == messages.ERRO_DIMENSAO_DIFERENTE.format(guardado=768, configurado=1024)


def test_no_migration_drops_data_without_a_backup_note():
    for arquivo in sorted(migrate.MIGRATIONS_DIR.glob("*.sql")):
        texto = arquivo.read_text(encoding="utf-8")
        if "drop " in texto.lower():
            assert "-- BACKUP:" in texto, f"{arquivo.name} tem DROP sem a nota -- BACKUP:"


def test_the_cli_prints_status_and_applies(scratch_database_url, capsys, monkeypatch):
    url = scratch_database_url()
    monkeypatch.setenv("DATABASE_URL", url)
    assert migrate.main(["--status"]) == 0
    assert "pendente" in capsys.readouterr().out
    assert migrate.main([]) == 0
    out = capsys.readouterr().out
    assert messages.MIGRACAO_APLICADA.format(arquivo=REAL[0]) in out
    assert migrate.main([]) == 0 and messages.MIGRACAO_NADA in capsys.readouterr().out
