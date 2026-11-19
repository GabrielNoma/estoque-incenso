"""Orders per phone number in the real database (data-model.md, tasks T005)."""
import psycopg
import pytest

from pedido.store import InvalidTransition, Store

ITENS = [{"produto_id": 1004, "nome": "Abre Caminho", "quantidade": 2.0},
         {"produto_id": 3027, "nome": "São Jorge", "quantidade": 0.5}]
LISTA = "Abre Caminho — 2 dz\nSão Jorge — 0,5 dz\n\nok ou não?"


def new(store, telefone="5511999990000", mensagem="2 dz abre caminho", itens=ITENS, lista=LISTA):
    return store.create_pedido(telefone, mensagem, itens, lista)


def test_a_new_order_waits_for_an_answer_and_keeps_everything_that_was_sent(store):
    order_id = new(store)
    pending = store.get_pending("5511999990000")
    assert pending["id"] == order_id and pending["estado"] == "aguardando"
    assert pending["mensagem"] == "2 dz abre caminho" and pending["lista"] == LISTA
    assert pending["itens"] == ITENS  # jsonb round-trip
    assert pending["resposta"] is None and pending["respondido_em"] is None
    assert isinstance(pending["criado_em"], str) and "T" in pending["criado_em"]


def test_there_is_no_pending_order_for_an_unknown_phone(store):
    assert store.get_pending("0000") is None


def test_a_new_order_replaces_the_pending_one_of_the_same_phone(store):
    first = new(store)
    second = new(store, mensagem="outra coisa")
    assert store.get_pending("5511999990000")["id"] == second
    old = store.get_pedido(first)
    assert old["estado"] == "substituido" and old["respondido_em"] is not None


def test_two_phones_never_interfere(store):
    a, b = new(store, telefone="111"), new(store, telefone="222")
    assert store.get_pending("111")["id"] == a and store.get_pending("222")["id"] == b
    store.set_estado(a, "confirmado", "ok")
    assert store.get_pending("222")["id"] == b  # b is untouched


@pytest.mark.parametrize("estado,resposta", [("confirmado", "ok"), ("recusado", "não")])
def test_an_answer_closes_the_order_and_is_stored(store, estado, resposta):
    order_id = new(store)
    store.set_estado(order_id, estado, resposta)
    closed = store.get_pedido(order_id)
    assert closed["estado"] == estado and closed["resposta"] == resposta and closed["respondido_em"]
    assert store.get_pending("5511999990000") is None


def test_a_closed_order_never_changes_again(store):
    order_id = new(store)
    store.set_estado(order_id, "confirmado", "ok")
    with pytest.raises(InvalidTransition):
        store.set_estado(order_id, "recusado", "não")
    assert store.get_pedido(order_id)["estado"] == "confirmado"


@pytest.mark.parametrize("estado", ["substituido", "aguardando", "inventado"])
def test_only_confirmado_and_recusado_can_be_set_by_an_answer(store, estado):
    order_id = new(store)
    with pytest.raises(InvalidTransition):
        store.set_estado(order_id, estado, "x")


def test_an_unknown_order_is_none(store):
    assert store.get_pedido(999999) is None


def test_a_new_store_instance_sees_the_data_like_after_a_restart(clean_db):
    order_id = new(Store(clean_db))
    assert Store(clean_db).get_pending("5511999990000")["id"] == order_id


def test_replacing_is_atomic_when_the_new_order_cannot_be_saved(store):
    first = new(store)
    with pytest.raises(Exception):
        new(store, itens=[{"nao_serializavel": {1, 2}}])  # fails after the old order was marked
    assert store.get_pending("5511999990000")["id"] == first  # the old one is still waiting
    assert store.get_pedido(first)["estado"] == "aguardando"
    assert len(store.list_pedidos()) == 1


def test_list_pedidos_is_newest_first_and_can_filter_by_phone(store):
    a, b, c = new(store, telefone="111"), new(store, telefone="222"), new(store, telefone="111")
    assert [p["id"] for p in store.list_pedidos()] == [c, b, a]
    assert [p["id"] for p in store.list_pedidos("111")] == [c, a]
