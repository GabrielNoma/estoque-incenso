"""ok: the Excel is generated and sent, and only then (Constitution III)."""
import io

import openpyxl
import pytest

from pedido import chains, config, messages
from pedido.conversa import Conversa

PHONE = "5511999990002"
ORDER = {"linhas": [{"texto": "ogum", "quantidade": 2}, {"texto": "abre caminho", "quantidade": 0.5}]}


@pytest.fixture
def calls(monkeypatch):
    spy = []
    real = chains.fill_template

    def counting(*args, **kwargs):
        spy.append(1)
        return real(*args, **kwargs)

    monkeypatch.setattr(chains, "fill_template", counting)
    return spy


@pytest.fixture
def bot(store, catalog, abbreviations, stub_chat):
    def make(*answers):
        return Conversa(store, catalog, stub_chat(list(answers)), abbreviations=abbreviations)
    return make


def test_no_file_is_generated_before_ok(bot, calls):
    conversa = bot(ORDER, {"linhas": [{"texto": "ogum", "quantidade": 1}]})
    conversa.responder(PHONE, "2 dz ogum e meia abre caminho")
    conversa.responder(PHONE, "1 dz ogum")  # another order, still no ok
    assert calls == []


@pytest.mark.parametrize("word", ["ok", "sim", "s", "confirmo", "isso", "certo", "blz", "pode", "beleza"])
def test_ok_sends_the_file_and_confirms_the_order(bot, store, word):
    conversa = bot(ORDER)
    first = conversa.responder(PHONE, "pedido")
    reply = conversa.responder(PHONE, word)
    assert reply.texto == messages.CONFIRMADO
    assert reply.arquivo_nome == f"pedido-{first.pedido_id}.xlsx"
    assert reply.arquivo_bytes[:2] == b"PK" and reply.pedido_id == first.pedido_id
    pedido = store.get_pedido(first.pedido_id)
    assert pedido["estado"] == "confirmado" and pedido["resposta"] == word and pedido["respondido_em"]
    assert store.get_pending(PHONE) is None


def test_the_file_has_the_quantities_the_formulas_and_a_blank_header(bot, catalog, by_name):
    conversa = bot(ORDER)
    conversa.responder(PHONE, "pedido")
    sheet = openpyxl.load_workbook(io.BytesIO(conversa.responder(PHONE, "ok").arquivo_bytes)).worksheets[0]
    assert sheet[by_name["Ogum"].celula_qtd].value == 2
    assert sheet[by_name["Abre Caminho"].celula_qtd].value == 0.5
    template = openpyxl.load_workbook(config.TEMPLATE_PATH).worksheets[0]
    formulas = [c for row in sheet.iter_rows() for c in row if isinstance(c.value, str) and c.value.startswith("=")]
    assert len(formulas) == 189
    for row in range(1, 4):
        for cell in sheet[row]:
            assert cell.value == template[cell.coordinate].value


def test_a_second_ok_and_an_ok_with_nothing_pending_get_the_invitation(bot, calls):
    conversa = bot(ORDER)
    assert conversa.responder(PHONE, "ok") == conversa.responder(PHONE, "ok")  # nothing pending
    conversa.responder(PHONE, "pedido")
    conversa.responder(PHONE, "ok")
    count = len(calls)
    again = conversa.responder(PHONE, "ok")
    assert again.texto == messages.ENVIE_PEDIDO and again.arquivo_bytes is None
    assert len(calls) == count
