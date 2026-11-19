"""Failures are one short neutral sentence; the pending order is never lost; the engine never raises."""
import psycopg
import pytest

from pedido import chains, messages
from pedido.conversa import Conversa
from pedido.llm import LLMNotConfigured

PHONE = "5511999990004"


def one(texto, quantidade=1):
    return {"linhas": [{"texto": texto, "quantidade": quantidade}]}


@pytest.fixture
def bot(store, catalog, abbreviations, stub_chat):
    def make(*answers):
        return Conversa(store, catalog, stub_chat(list(answers)), abbreviations=abbreviations)
    return make


def test_the_model_failing_twice_replies_erro_leitura_and_keeps_the_pending_order(bot, store):
    conversa = bot(one("ogum"), RuntimeError("a"), RuntimeError("b"))
    first = conversa.responder(PHONE, "ogum")
    reply = conversa.responder(PHONE, "abre caminho")
    assert reply.texto == messages.ERRO_LEITURA and reply.arquivo_bytes is None
    assert store.get_pending(PHONE)["id"] == first.pedido_id


def test_an_unconfigured_provider_replies_erro_leitura(bot):
    reply = bot(LLMNotConfigured("sem chave")).responder(PHONE, "ogum")
    assert reply.texto == messages.ERRO_LEITURA


def test_a_failing_excel_replies_erro_planilha_and_a_later_ok_sends_the_file(bot, store, monkeypatch):
    conversa = bot(one("ogum"))
    first = conversa.responder(PHONE, "ogum")
    real = chains.fill_template
    monkeypatch.setattr(chains, "fill_template", lambda *a, **k: (_ for _ in ()).throw(OSError("disco")))
    reply = conversa.responder(PHONE, "ok")
    assert reply.texto == messages.ERRO_PLANILHA and reply.arquivo_bytes is None
    assert store.get_pending(PHONE)["id"] == first.pedido_id
    monkeypatch.setattr(chains, "fill_template", real)
    assert conversa.responder(PHONE, "ok").arquivo_bytes[:2] == b"PK"


class BrokenStore:
    def __getattr__(self, name):
        def fail(*args, **kwargs):
            raise psycopg.OperationalError("banco fora")
        return fail


@pytest.mark.parametrize("text", ["ogum", "ok", "não"])
def test_a_database_error_replies_erro_banco(catalog, abbreviations, stub_chat, text):
    conversa = Conversa(BrokenStore(), catalog, stub_chat([one("ogum")]), abbreviations=abbreviations)
    assert conversa.responder(PHONE, text).texto == messages.ERRO_BANCO


def test_an_unexpected_exception_never_propagates(catalog, abbreviations, stub_chat):
    class Exploding:
        def get_pending(self, *_):
            raise ValueError("inesperado")
    conversa = Conversa(Exploding(), catalog, stub_chat(), abbreviations=abbreviations)
    reply = conversa.responder(PHONE, "ok")
    assert reply.texto == messages.ERRO_BANCO and reply.arquivo_bytes is None
