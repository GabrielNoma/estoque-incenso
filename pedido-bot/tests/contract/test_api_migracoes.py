"""The application refuses to start when the database schema is not ready (Constitution VI)."""
import pytest

from pedido import messages, migrate
from pedido.db import StartupError
from pedido.startup import check_all
from pedido.web.app import create_app


def criar(url, stub_chat):
    return create_app(database_url=url, chat_model=stub_chat([]), embedder=None, api_keys=None)


@pytest.mark.parametrize("ambiente", ["producao", "local"])
def test_pending_migrations_refuse_the_start_in_production_and_outside_it(scratch_database_url, stub_chat,
                                                                           monkeypatch, ambiente):
    monkeypatch.setenv("ENVIRONMENT", ambiente)
    monkeypatch.delenv("MIGRATE_ON_START", raising=False)
    url = scratch_database_url()
    with pytest.raises(StartupError) as error:
        create_app(database_url=url, chat_model=stub_chat([]), embedder=None, api_keys="a:conversa:" + "k" * 40)
    assert "python -m pedido.migrate" in str(error.value)


def test_an_altered_applied_migration_refuses_the_start_and_names_the_file(scratch_database_url, stub_chat,
                                                                           monkeypatch, tmp_path):
    monkeypatch.delenv("ENVIRONMENT", raising=False)
    arquivo = tmp_path / "0001_a.sql"
    arquivo.write_text("select 1;", encoding="utf-8")
    monkeypatch.setattr(migrate, "MIGRATIONS_DIR", tmp_path)
    url = scratch_database_url()
    migrate.aplicar(url, 1024)
    arquivo.write_text("select 2;", encoding="utf-8")
    with pytest.raises(StartupError) as error:
        criar(url, stub_chat)
    assert str(error.value) == messages.ERRO_MIGRACAO_ALTERADA.format(arquivo="0001_a.sql")


def test_migrating_at_start_is_allowed_only_by_the_explicit_setting(scratch_database_url, stub_chat, monkeypatch):
    monkeypatch.delenv("ENVIRONMENT", raising=False)
    url = scratch_database_url()
    monkeypatch.setenv("MIGRATE_ON_START", "true")
    assert criar(url, stub_chat) is not None  # applied and started
    monkeypatch.delenv("MIGRATE_ON_START")
    assert criar(url, stub_chat) is not None  # nothing pending now


def test_the_startup_check_of_the_command_line_also_refuses(scratch_database_url, monkeypatch):
    monkeypatch.delenv("MIGRATE_ON_START", raising=False)
    monkeypatch.delenv("ENVIRONMENT", raising=False)
    url = scratch_database_url()
    with pytest.raises(StartupError):
        check_all({"DATABASE_URL": url, "LLM_PROVIDER": "anthropic"})
    migrate.aplicar(url, 1024)
    check_all({"DATABASE_URL": url, "LLM_PROVIDER": "anthropic"})
