"""Database module: schema, guarded cleanup of the old tables, startup check (tasks T003)."""
import pytest

from pedido import db, messages, migrate

TABLES = {"catalog", "pedidos", "apelidos", "modelos", "uso_diario", "schema_migrations"}
LEGACY = {"aliases", "runs", "run_lines", "memoria_linhas", "memoria_mensagens"}


def tables(url):
    with db.connect(url) as conn:
        rows = conn.execute("select table_name from information_schema.tables "
                            "where table_schema = 'pedido'").fetchall()
    return {r[0] for r in rows}


def extensions(url):
    with db.connect(url) as conn:
        return {r[0] for r in conn.execute("select extname from pg_extension").fetchall()}


def make_legacy(url):
    """The tables of features 001/002, with a vector column, as they existed before."""
    with db.connect(url) as conn:
        conn.execute("create extension if not exists vector; create schema if not exists pedido;"
                     "create table pedido.aliases (texto_normalizado text primary key, produto_id int);"
                     "create table pedido.runs (id bigint primary key, mensagem text);"
                     "create table pedido.run_lines (id bigint primary key, run_id bigint);"
                     "create table pedido.memoria_linhas (id bigint primary key, embedding vector(8));"
                     "create table pedido.memoria_mensagens (id bigint primary key, embedding vector(8));"
                     "insert into pedido.runs values (1, 'demonstracao');")


def test_apply_schema_creates_the_schema_and_exactly_the_six_tables(scratch_database_url):
    url = scratch_database_url()
    db.apply_schema(url)
    assert tables(url) == TABLES


def test_apply_schema_is_idempotent_and_keeps_the_orders(scratch_database_url):
    url = scratch_database_url()
    db.apply_schema(url)
    with db.connect(url) as conn:
        conn.execute("insert into pedido.pedidos (telefone, mensagem, itens, lista) "
                     "values ('551100', '2 dz ogum', '[]', 'x')")
    db.apply_schema(url)
    db.apply_schema(url)
    with db.connect(url) as conn:
        assert conn.execute("select count(*) from pedido.pedidos").fetchone()[0] == 1


def test_row_level_security_is_enabled_on_every_table_without_policies(scratch_database_url):
    url = scratch_database_url()
    db.apply_schema(url)
    with db.connect(url) as conn:
        rls = dict(conn.execute("select c.relname, c.relrowsecurity from pg_class c "
                                "join pg_namespace n on n.oid = c.relnamespace "
                                "where n.nspname = 'pedido' and c.relkind = 'r'").fetchall())
        policies = conn.execute("select count(*) from pg_policies where schemaname = 'pedido'").fetchone()[0]
    assert set(rls) == TABLES and all(rls.values()) and policies == 0


def test_the_legacy_tables_are_dropped_once_when_present(scratch_database_url):
    url = scratch_database_url()
    make_legacy(url)
    assert LEGACY <= tables(url) and "vector" in extensions(url)
    db.apply_schema(url)
    assert tables(url) == TABLES and "vector" in extensions(url)


def test_the_cleanup_does_nothing_without_legacy_tables(scratch_database_url):
    url = scratch_database_url()
    with db.connect(url) as conn:
        conn.execute("create extension if not exists vector")  # an unrelated use of the extension
    db.apply_schema(url)
    assert tables(url) == TABLES and "vector" in extensions(url)  # left alone: nothing legacy to clean


def test_check_database_accepts_a_migrated_database(scratch_database_url):
    url = scratch_database_url()
    db.apply_schema(url)
    db.check_database(url)


def test_an_unreachable_database_refuses_with_the_portuguese_message():
    with pytest.raises(db.StartupError) as error:
        db.check_database("postgresql://pedido:pedido@127.0.0.1:1/pedido")
    assert str(error.value) == messages.ERRO_BANCO_INACESSIVEL


def test_a_missing_url_refuses_with_the_portuguese_message():
    with pytest.raises(db.StartupError) as error:
        db.check_database(None)
    assert str(error.value) == messages.ERRO_BANCO_NAO_CONFIGURADO


def test_connections_use_no_prepared_statements(scratch_database_url):
    url = scratch_database_url()
    db.apply_schema(url)
    with db.connect(url) as conn:
        assert conn.prepare_threshold is None


# -- feature 004: the vector extension and the nickname memory -------------------------------------------
def columns(url, table):
    with db.connect(url) as conn:
        rows = conn.execute("select column_name from information_schema.columns "
                            "where table_schema = 'pedido' and table_name = %s", (table,)).fetchall()
    return {r[0] for r in rows}


def test_apply_schema_creates_the_vector_extension_the_memory_table_and_the_lines_column(scratch_database_url):
    url = scratch_database_url()
    db.apply_schema(url, 1024)
    assert tables(url) == TABLES
    assert "vector" in extensions(url)
    assert {"texto_normalizado", "produto_id", "embedding", "modelo", "positivos", "negativos",
            "status"} <= columns(url, "apelidos")
    assert "linhas" in columns(url, "pedidos")


def test_the_apelidos_pair_is_unique_and_row_level_security_is_on(scratch_database_url):
    import psycopg

    url = scratch_database_url()
    db.apply_schema(url, 1024)
    with db.connect(url) as conn:
        conn.execute("insert into pedido.apelidos (texto_normalizado, produto_id) values ('a', 1)")
    with pytest.raises(psycopg.errors.UniqueViolation), db.connect(url) as conn:
        conn.execute("insert into pedido.apelidos (texto_normalizado, produto_id) values ('a', 1)")
    with db.connect(url) as conn:
        assert conn.execute("select relrowsecurity from pg_class where relname = 'apelidos'").fetchone()[0]


def test_a_003_database_is_upgraded_keeping_every_order(scratch_database_url):
    url = scratch_database_url()
    with db.connect(url) as conn:  # the schema of feature 003, as it was
        conn.execute("create schema pedido; create table pedido.pedidos (id bigint generated by default as "
                     "identity primary key, telefone text not null, mensagem text not null, itens jsonb not null, "
                     "lista text not null, estado text not null default 'aguardando', resposta text, "
                     "criado_em timestamptz not null default now(), respondido_em timestamptz);"
                     "insert into pedido.pedidos (telefone, mensagem, itens, lista) values ('1', 'm', '[]', 'l')")
    db.apply_schema(url, 1024)
    with db.connect(url) as conn:
        assert conn.execute("select count(*) from pedido.pedidos").fetchone()[0] == 1
        assert conn.execute("select linhas from pedido.pedidos").fetchone()[0] == []


def test_the_legacy_cleanup_does_not_drop_the_vector_extension(scratch_database_url):
    url = scratch_database_url()
    make_legacy(url)
    db.apply_schema(url, 1024)
    assert not (LEGACY & tables(url)) and "vector" in extensions(url)


def test_a_different_dimension_is_refused_in_portuguese(scratch_database_url):
    url = scratch_database_url()
    db.apply_schema(url, 1024)
    with pytest.raises(db.StartupError) as error:
        db.check_database(url, 768)
    assert str(error.value) == messages.ERRO_DIMENSAO_DIFERENTE.format(guardado=1024, configurado=768)
    db.check_database(url, 1024)  # the same size is fine


def test_a_missing_vector_extension_is_refused_in_portuguese(scratch_database_url, monkeypatch, tmp_path):
    url = scratch_database_url()
    (tmp_path / "0001_ruim.sql").write_text("create extension nao_existe_xyz;", encoding="utf-8")
    monkeypatch.setattr(migrate, "MIGRATIONS_DIR", tmp_path)
    monkeypatch.setenv("MIGRATE_ON_START", "true")
    with pytest.raises(db.StartupError) as error:
        db.check_database(url, 1024)
    assert str(error.value) == messages.ERRO_VECTOR_INDISPONIVEL


# -- feature 005: the managed model ---------------------------------------------------------------------
def test_the_schema_creates_modelos_and_the_new_columns(scratch_database_url):
    url = scratch_database_url()
    db.apply_schema(url, 1024)
    assert {"versao", "arquivo", "conteudo", "produtos", "ativo", "criado_em"} <= columns(url, "modelos")
    assert "modelo_versao" in columns(url, "pedidos") and "produto_nome" in columns(url, "apelidos")


def test_at_most_one_model_is_active_and_versions_are_unique(scratch_database_url):
    import psycopg

    url = scratch_database_url()
    db.apply_schema(url, 1024)
    with db.connect(url) as conn:
        conn.execute("insert into pedido.modelos (versao, arquivo, conteudo, produtos, ativo) "
                     "values (1, 'a.xlsx', 'x', 1, true), (2, 'b.xlsx', 'x', 1, false)")
    with pytest.raises(psycopg.errors.UniqueViolation), db.connect(url) as conn:
        conn.execute("insert into pedido.modelos (versao, arquivo, conteudo, produtos, ativo) "
                     "values (3, 'c.xlsx', 'x', 1, true)")
    with pytest.raises(psycopg.errors.UniqueViolation), db.connect(url) as conn:
        conn.execute("insert into pedido.modelos (versao, arquivo, conteudo, produtos) values (2, 'd', 'x', 1)")


def test_a_004_database_is_upgraded_keeping_orders_and_nicknames(scratch_database_url):
    url = scratch_database_url()
    db.apply_schema(url, 1024)
    with db.connect(url) as conn:  # what a 004 database looks like
        conn.execute("alter table pedido.pedidos drop column modelo_versao; "
                     "alter table pedido.apelidos drop column produto_nome; drop table pedido.modelos;"
                     "delete from pedido.schema_migrations;"  # as a database from before the migrations
                     "insert into pedido.pedidos (telefone, mensagem, itens, lista) values ('1', 'm', '[]', 'l');"
                     "insert into pedido.apelidos (texto_normalizado, produto_id, positivos) values ('a', 1, 2)")
    db.apply_schema(url, 1024)
    with db.connect(url) as conn:
        assert conn.execute("select count(*) from pedido.pedidos").fetchone()[0] == 1
        assert conn.execute("select positivos from pedido.apelidos").fetchone()[0] == 2
    assert "modelos" in tables(url) and "produto_nome" in columns(url, "apelidos")


# -- feature 006: check_database verifies migrations instead of applying them ---------------------------------
def test_check_database_refuses_pending_migrations_unless_migrating_at_start_is_allowed(scratch_database_url, monkeypatch):
    url = scratch_database_url()
    monkeypatch.delenv("MIGRATE_ON_START", raising=False)
    with pytest.raises(db.StartupError) as error:
        db.check_database(url, 1024)
    assert "python -m pedido.migrate" in str(error.value)
    monkeypatch.setenv("MIGRATE_ON_START", "true")
    db.check_database(url, 1024)  # applies and passes
    monkeypatch.delenv("MIGRATE_ON_START")
    db.check_database(url, 1024)  # nothing pending now


def test_check_database_refuses_an_altered_applied_migration(scratch_database_url, monkeypatch, tmp_path):
    url = scratch_database_url()
    arquivo = tmp_path / "0001_a.sql"
    arquivo.write_text("select 1;", encoding="utf-8")
    monkeypatch.setattr(migrate, "MIGRATIONS_DIR", tmp_path)
    migrate.aplicar(url, 1024)
    arquivo.write_text("select 2;", encoding="utf-8")
    with pytest.raises(db.StartupError) as error:
        db.check_database(url, 1024)
    assert str(error.value) == messages.ERRO_MIGRACAO_ALTERADA.format(arquivo="0001_a.sql")
