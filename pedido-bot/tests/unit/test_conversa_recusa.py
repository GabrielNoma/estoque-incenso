"""não, a new order that replaces the pending one, and the neutral replies."""
import pytest

from pedido import messages
from pedido.conversa import Conversa

PHONE = "5511999990003"


@pytest.fixture
def bot(store, catalog, abbreviations, stub_chat):
    def make(*answers):
        return Conversa(store, catalog, stub_chat(list(answers)), abbreviations=abbreviations)
    return make


def one(texto, quantidade=1):
    return {"linhas": [{"texto": texto, "quantidade": quantidade}]}


@pytest.mark.parametrize("word", ["não", "nao", "n", "cancelar", "cancela", "errado", "negativo"])
def test_nao_discards_the_pending_order(bot, store, word):
    conversa = bot(one("ogum"))
    first = conversa.responder(PHONE, "ogum")
    reply = conversa.responder(PHONE, word)
    assert reply.texto == messages.CANCELADO and reply.arquivo_bytes is None
    assert store.get_pedido(first.pedido_id)["estado"] == "recusado"
    assert store.get_pending(PHONE) is None


def test_nao_with_nothing_pending_gets_the_invitation(bot):
    assert bot().responder(PHONE, "não").texto == messages.ENVIE_PEDIDO


def test_a_new_order_replaces_the_pending_one_and_a_later_ok_confirms_only_the_new(bot, store):
    conversa = bot(one("ogum", 1), one("abre caminho", 3))
    first = conversa.responder(PHONE, "1 dz ogum")
    second = conversa.responder(PHONE, "3 dz abre caminho")
    assert "Abre Caminho — 3 dz" in second.texto and "Ogum" not in second.texto
    assert store.get_pedido(first.pedido_id)["estado"] == "substituido"
    done = conversa.responder(PHONE, "ok")
    assert done.pedido_id == second.pedido_id
    assert store.get_pedido(second.pedido_id)["estado"] == "confirmado"
    assert store.get_pedido(first.pedido_id)["estado"] == "substituido"


def test_a_message_without_items_gets_sem_itens_and_keeps_the_pending_order(bot, store):
    conversa = bot(one("ogum"), {"linhas": []})
    first = conversa.responder(PHONE, "ogum")
    reply = conversa.responder(PHONE, "bom dia")
    assert reply.texto == messages.SEM_ITENS and reply.arquivo_bytes is None
    assert store.get_pending(PHONE)["id"] == first.pedido_id


def test_an_empty_text_gets_sem_itens_without_calling_the_model(bot, stub_chat):
    conversa = bot()  # no canned answer: any model call would fail
    assert conversa.responder(PHONE, "   ").texto == messages.SEM_ITENS


def test_each_phone_has_its_own_pending_order(bot, store):
    conversa = bot(one("ogum"), one("abre caminho"))
    a = conversa.responder("1", "ogum")
    b = conversa.responder("2", "abre caminho")
    assert store.get_pending("1")["id"] == a.pedido_id and store.get_pending("2")["id"] == b.pedido_id
