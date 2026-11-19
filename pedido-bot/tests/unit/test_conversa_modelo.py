"""The conversation with a managed model: model problems are one neutral sentence (Constitution III)."""
import io

import openpyxl
import pytest

from pedido import messages
from pedido.conversa import Conversa
from pedido.modelos import ModeloService

PHONE = "5511999990011"


def one(texto, quantidade=1):
    return {"linhas": [{"texto": texto, "quantidade": quantidade}]}


@pytest.fixture
def setup(store, abbreviations, stub_chat):
    service = ModeloService(store, abbreviations)
    service.iniciar()

    def build(*answers):
        return Conversa(store, service, stub_chat(list(answers)), abbreviations=abbreviations)

    return build, service


def test_an_order_after_an_import_can_name_the_new_product(setup, variante):
    build, service = setup
    bot = build(one("incenso teste", 2))
    service.importar(variante.com_produto_novo("Incenso Teste"), "novo.xlsx")
    assert bot.responder(PHONE, "2 dz incenso teste").texto == "Incenso Teste — 2 dz\n\nok ou não?"


def test_the_replies_for_normal_orders_are_those_of_a_static_model(setup, store, catalog, abbreviations, stub_chat):
    build, _ = setup
    respostas = [one("ogum", 2), one("abre camino"), one("arruda", 3)]
    gerenciado = build(*respostas)
    estatico = Conversa(store, catalog, stub_chat(list(respostas)), abbreviations=abbreviations)
    for telefone, texto in (("1", "2 ogum"), ("1", "ok"), ("2", "abre camino"), ("2", "não"), ("3", "3 arruda")):
        a, b = gerenciado.responder(f"g{telefone}", texto), estatico.responder(f"e{telefone}", texto)  # own phones: one shared store
        assert (a.texto, a.arquivo_bytes is not None) == (b.texto, b.arquivo_bytes is not None)


def test_a_model_that_cannot_be_read_gets_the_check_the_model_sentence(setup, store, variante):
    build, _ = setup
    bot = build(one("ogum"))  # no second answer: the model must not even be called for the broken case
    first = bot.responder(PHONE, "ogum")
    store.salvar_modelo("quebrado.xlsx", variante.LIXO, 0)
    reply = bot.responder(PHONE, "arruda")
    assert reply.texto == messages.MODELO_INVALIDO and reply.arquivo_bytes is None
    assert store.get_pending(PHONE)["id"] == first.pedido_id  # the pending order is kept
    assert len(store.list_pedidos()) == 1


def test_a_model_without_products_gets_the_same_sentence(setup, store, variante):
    build, _ = setup
    store.salvar_modelo("vazio.xlsx", variante.sem_produtos(), 0)
    assert build().responder(PHONE, "ogum").texto == messages.MODELO_INVALIDO


def test_ok_with_a_product_that_left_the_model_asks_to_check_it_and_keeps_the_order(setup, store, variante):
    build, service = setup
    bot = build(one("ogum", 2), one("arruda", 3))
    pedido = bot.responder(PHONE, "2 dz ogum")
    service.importar(variante.sem_produto("Ogum"), "sem-ogum.xlsx")
    reply = bot.responder(PHONE, "ok")
    assert reply.texto == messages.MODELO_PRODUTO_AUSENTE and reply.arquivo_bytes is None
    assert store.get_pending(PHONE)["id"] == pedido.pedido_id
    nova = bot.responder(PHONE, "3 dz arruda")  # a new order replaces it and works with the new model
    assert nova.texto == "Arruda — 3 dz\n\nok ou não?"
    assert bot.responder(PHONE, "ok").arquivo_bytes[:2] == b"PK"


def test_ok_with_a_product_renamed_at_its_position_is_also_a_problem(setup, variante):
    build, service = setup
    bot = build(one("ogum"))
    bot.responder(PHONE, "ogum")
    service.importar(variante.renomeado("Ogum", "Ogum Forte"), "renomeado.xlsx")
    assert bot.responder(PHONE, "ok").texto == messages.MODELO_PRODUTO_AUSENTE


def test_ok_with_all_products_still_there_fills_the_new_model(setup, store, variante):
    build, service = setup
    bot = build(one("incenso teste", 4))
    service.importar(variante.com_produto_novo("Incenso Teste"), "novo.xlsx")
    bot.responder(PHONE, "4 dz incenso teste")
    service.importar(variante.com_produto_novo("Incenso Teste"), "novo2.xlsx")  # another model, same products
    reply = bot.responder(PHONE, "ok")
    assert reply.texto == messages.CONFIRMADO
    produto = next(p for p in service.atual().catalog if p.nome == "Incenso Teste")
    sheet = openpyxl.load_workbook(io.BytesIO(reply.arquivo_bytes)).worksheets[0]
    assert sheet[produto.celula_qtd].value == 4
    assert store.get_pedido(reply.pedido_id)["modelo_versao"] == 3


def test_closest_match_is_untouched_no_doubt_is_ever_reported(setup):
    build, _ = setup
    reply = build(one("abre camino")).responder(PHONE, "abre camino")
    assert reply.texto == "Abre Caminho — 1 dz\n\nok ou não?"
