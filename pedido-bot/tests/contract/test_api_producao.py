"""Production switches: no page, no docs, refuse to start without keys (Constitution IX)."""
import logging

import pytest
from fastapi.testclient import TestClient

from pedido import messages
from pedido.db import StartupError
from pedido.web.app import create_app

KEY = "p" * 40
API_KEYS = f"estoque:conversa+modelo:{KEY}"


@pytest.fixture
def producao(monkeypatch):
    monkeypatch.setenv("ENVIRONMENT", "producao")


def app(clean_db, stub_chat, **kwargs):
    return create_app(database_url=clean_db, chat_model=stub_chat([]), embedder=None, **kwargs)


@pytest.mark.parametrize("caminho", ["/", "/static/app.js", "/static/app.css", "/docs", "/redoc", "/openapi.json"])
def test_the_page_its_files_and_the_docs_do_not_exist_in_production(producao, clean_db, stub_chat, caminho):
    http = TestClient(app(clean_db, stub_chat, api_keys=API_KEYS))
    assert http.get(caminho, headers={"X-API-Key": KEY}).status_code == 404


def test_the_api_still_works_in_production_with_the_key(producao, clean_db, stub_chat):
    http = TestClient(app(clean_db, stub_chat, api_keys=API_KEYS))
    assert http.get("/api/modelo/info", headers={"X-API-Key": KEY}).status_code == 200
    assert http.get("/api/modelo/info").status_code == 401


def test_production_refuses_to_start_without_a_valid_key(producao, clean_db, stub_chat):
    for chaves in (None, "", "   "):
        with pytest.raises(StartupError) as error:
            app(clean_db, stub_chat, api_keys=chaves)
        assert str(error.value) == messages.ERRO_CHAVES_AUSENTES
    with pytest.raises(StartupError):
        app(clean_db, stub_chat, api_keys="curta:conversa:xx")


def test_outside_production_the_page_and_the_docs_exist(monkeypatch, clean_db, stub_chat):
    monkeypatch.delenv("ENVIRONMENT", raising=False)
    http = TestClient(app(clean_db, stub_chat))
    assert http.get("/").status_code == 200 and http.get("/docs").status_code == 200


def test_outside_production_keys_configured_means_control_is_on(monkeypatch, clean_db, stub_chat):
    monkeypatch.delenv("ENVIRONMENT", raising=False)
    http = TestClient(app(clean_db, stub_chat, api_keys=API_KEYS))
    assert http.get("/api/modelo/info").status_code == 401


def test_outside_production_without_keys_starts_with_a_warning(monkeypatch, clean_db, stub_chat, caplog):
    monkeypatch.delenv("ENVIRONMENT", raising=False)
    caplog.set_level(logging.WARNING)
    app(clean_db, stub_chat)
    assert "controle de acesso desligado" in caplog.text
