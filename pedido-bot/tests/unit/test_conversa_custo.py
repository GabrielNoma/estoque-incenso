"""Cost and abuse guards inside the conversation (Constitution VIII): daily limit and concurrency cap."""
import logging
import threading
import time
from datetime import datetime, timedelta, timezone

import psycopg
import pytest

from pedido import guardrails, messages
from pedido.conversa import Conversa
from pedido.extract import ExtracaoPedido

PHONE = "5511999990020"


def one(texto="ogum", quantidade=1):
    return {"linhas": [{"texto": texto, "quantidade": quantidade}]}


class Relogio:
    def __init__(self):
        self.agora = datetime(2026, 11, 18, 15, 0, tzinfo=timezone.utc)

    def __call__(self):
        return self.agora


def test_a_message_over_the_daily_limit_gets_the_neutral_sentence_without_calling_the_model(
        store, catalog, abbreviations, stub_chat, monkeypatch):
    monkeypatch.setenv("LIMITE_DIARIO_CONVERSA", "3")
    chat = stub_chat([one("ogum"), one("arruda")])  # only two readings exist: a 3rd call would fail the test
    relogio = Relogio()
    bot = Conversa(store, catalog, chat, abbreviations=abbreviations, agora=relogio,
                   limitador=guardrails.RateLimiter(limite=1000))
    bot.responder(PHONE, "ogum")  # message 1
    assert bot.responder(PHONE, "ok").arquivo_bytes  # message 2
    pendente = bot.responder(PHONE, "arruda")  # message 3: a new order waits for an answer
    limitada = bot.responder(PHONE, "mais um pedido")  # message 4: over the limit of 3
    assert limitada.texto == messages.LIMITE_DIARIO and limitada.arquivo_bytes is None
    assert chat.calls == 2  # the limited message never reached the language model
    assert store.get_pending(PHONE)["id"] == pendente.pedido_id  # the pending order was not lost
    relogio.agora += timedelta(days=1)
    assert bot.responder(PHONE, "ok").arquivo_bytes  # the next day it works again and confirms it


def test_the_limit_is_per_conversation(store, catalog, abbreviations, stub_chat, monkeypatch):
    monkeypatch.setenv("LIMITE_DIARIO_CONVERSA", "1")
    bot = Conversa(store, catalog, stub_chat([one(), one()]), abbreviations=abbreviations, agora=Relogio(),
                   limitador=guardrails.RateLimiter(limite=1000))
    assert bot.responder("1", "ogum").texto.endswith("ok ou não?")
    assert bot.responder("1", "ogum").texto == messages.LIMITE_DIARIO
    assert bot.responder("2", "ogum").texto.endswith("ok ou não?")


def test_a_database_failure_in_the_counter_is_a_database_error_not_the_limit_sentence(
        store, catalog, abbreviations, stub_chat, monkeypatch):
    bot = Conversa(store, catalog, stub_chat([one()]), abbreviations=abbreviations)

    def cair(*_a, **_k):
        raise psycopg.OperationalError("banco fora")

    monkeypatch.setattr(store, "registrar_mensagem", cair)
    assert bot.responder(PHONE, "ogum").texto == messages.ERRO_BANCO


class ChatLento:
    """A chat model that takes its time and records how many calls are inside at once."""

    def __init__(self, demora=0.15):
        self.demora, self.dentro, self.pico, self.chamadas = demora, 0, 0, 0
        self._trava = threading.Lock()

    def with_structured_output(self, schema, **_kw):
        chat = self

        class Chamada:
            def invoke(self, _prompt):
                with chat._trava:
                    chat.dentro += 1
                    chat.chamadas += 1
                    chat.pico = max(chat.pico, chat.dentro)
                time.sleep(chat.demora)
                with chat._trava:
                    chat.dentro -= 1
                return ExtracaoPedido.model_validate(one())

        return Chamada()


def test_a_burst_never_runs_more_model_calls_at_once_than_the_limit(store, catalog, abbreviations, monkeypatch):
    monkeypatch.setenv("MAX_LLM_CONCORRENTES", "2")
    monkeypatch.setenv("ESPERA_LLM_SEGUNDOS", "20")
    chat = ChatLento()
    bot = Conversa(store, catalog, chat, abbreviations=abbreviations, limitador=guardrails.RateLimiter(limite=1000))
    respostas = []
    fios = [threading.Thread(target=lambda i=i: respostas.append(bot.responder(f"9{i}", "ogum"))) for i in range(8)]
    for f in fios:
        f.start()
    for f in fios:
        f.join()
    assert chat.pico <= 2 and chat.chamadas == 8
    assert all(r.texto.endswith("ok ou não?") for r in respostas)


def test_a_message_that_waits_too_long_for_a_slot_gets_the_busy_sentence_and_ok_nao_are_not_blocked(
        store, catalog, abbreviations, caplog):
    caplog.set_level(logging.DEBUG)
    chat = ChatLento(demora=0.6)
    bot = Conversa(store, catalog, chat, abbreviations=abbreviations, limitador=guardrails.RateLimiter(limite=1000),
                   concorrencia=guardrails.LimiteConcorrencia(maximo=1, espera=0.1))
    primeira = []
    fio = threading.Thread(target=lambda: primeira.append(bot.responder("a", "ogum")))
    fio.start()
    time.sleep(0.15)  # the only slot is taken
    ocupado = bot.responder("segredo-do-telefone", "texto-secreto-do-cliente")
    assert ocupado.texto == messages.OCUPADO and chat.chamadas == 1
    assert bot.responder("b", "não").texto == messages.ENVIE_PEDIDO  # no model needed: not blocked
    fio.join()
    assert primeira[0].texto.endswith("ok ou não?")
    assert "guardrail=ocupado" in caplog.text
    assert "segredo-do-telefone" not in caplog.text and "texto-secreto-do-cliente" not in caplog.text


def test_limite_concorrencia_releases_its_slot_after_an_error():
    limite = guardrails.LimiteConcorrencia(maximo=1, espera=0.1)
    with pytest.raises(ValueError):
        with limite.vaga():
            raise ValueError("falhou")
    with limite.vaga():  # the slot is free again
        pass
