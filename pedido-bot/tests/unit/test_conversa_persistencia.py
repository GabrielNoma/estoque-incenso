"""Orders live in the database, not in the engine (Constitution VI)."""
import os

import pytest

from pedido import messages
from pedido.conversa import Conversa
from pedido.store import Store


def make(url, catalog, abbreviations, stub_chat, *answers):
    return Conversa(Store(url), catalog, stub_chat(list(answers)), abbreviations=abbreviations)


def one(texto, quantidade=1):
    return {"linhas": [{"texto": texto, "quantidade": quantidade}]}


def test_ok_still_works_after_a_restart(clean_db, catalog, abbreviations, stub_chat):
    before = make(clean_db, catalog, abbreviations, stub_chat, one("ogum", 2))
    first = before.responder("5511", "2 dz ogum")
    after = make(clean_db, catalog, abbreviations, stub_chat)  # a brand-new engine and store
    reply = after.responder("5511", "ok")
    assert reply.texto == messages.CONFIRMADO and reply.pedido_id == first.pedido_id and reply.arquivo_bytes


def test_two_phones_confirm_independently(clean_db, catalog, abbreviations, stub_chat):
    bot = make(clean_db, catalog, abbreviations, stub_chat, one("ogum"), one("abre caminho"))
    a = bot.responder("1", "ogum")
    b = bot.responder("2", "abre caminho")
    assert "Ogum" in a.texto and "Ogum" not in b.texto
    assert bot.responder("2", "ok").pedido_id == b.pedido_id
    assert bot.responder("1", "ok").pedido_id == a.pedido_id


def test_the_stored_order_keeps_message_list_answer_and_state(clean_db, catalog, abbreviations, stub_chat):
    bot = make(clean_db, catalog, abbreviations, stub_chat, one("ogum", 2))
    first = bot.responder("5511", "2 dz ogum")
    bot.responder("5511", "ok")
    row = Store(clean_db).get_pedido(first.pedido_id)
    assert (row["mensagem"], row["lista"], row["resposta"], row["estado"]) == (
        "2 dz ogum", first.texto, "ok", "confirmado")
    assert row["itens"][0]["nome"] == "Ogum" and row["itens"][0]["quantidade"] == 2


def test_nothing_is_written_to_local_files(clean_db, catalog, abbreviations, stub_chat, tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    bot = make(clean_db, catalog, abbreviations, stub_chat, one("ogum"))
    bot.responder("5511", "ogum")
    bot.responder("5511", "ok")
    assert os.listdir(tmp_path) == []
