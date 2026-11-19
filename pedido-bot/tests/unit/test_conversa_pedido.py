"""Reading the customer's reply and the order path of the conversation (Constitution III)."""
import pytest

from pedido.conversa import Conversa, interpretar

PHONE = "5511999990001"


@pytest.mark.parametrize("text", ["ok", "OK", "Ok!", "okay", "sim", "s", "confirmo", "confirmado", "isso",
                                  "certo", "blz", "pode", "beleza", "  Beleza.  "])
def test_confirmations(text):
    assert interpretar(text) == "ok"


@pytest.mark.parametrize("text", ["não", "Não!", "nao", "NAO", "n", "cancelar", "cancela", "errado", "negativo"])
def test_refusals(text):
    assert interpretar(text) == "nao"


@pytest.mark.parametrize("text", ["ok obrigado", "2 dz ogum", "sim 2 dz ogum", "", "   ", "bom dia"])
def test_anything_else_is_an_order(text):
    assert interpretar(text) == "pedido"


@pytest.fixture
def conversa(store, catalog, abbreviations, stub_chat):
    def make(*answers):
        return Conversa(store, catalog, stub_chat(list(answers)), abbreviations=abbreviations)
    return make


def test_an_order_gets_exactly_the_list_and_the_question(conversa, store):
    bot = conversa({"linhas": [{"texto": "ogum", "quantidade": 2}, {"texto": "abre caminho", "quantidade": 0.5}]})
    reply = bot.responder(PHONE, "2 dz ogum e meia dz abre caminho")
    lines = reply.texto.split("\n")
    assert lines[-2:] == ["", "ok ou não?"]
    assert set(lines[:-2]) == {"Abre Caminho — 0,5 dz", "Ogum — 2 dz"}
    assert "?" not in "\n".join(lines[:-1])
    assert reply.arquivo_nome is None and reply.arquivo_bytes is None
    pending = store.get_pending(PHONE)
    assert pending["estado"] == "aguardando" and pending["lista"] == reply.texto
    assert reply.pedido_id == pending["id"]


def test_an_order_with_unrelated_text_is_still_matched(conversa):
    reply = conversa({"linhas": [{"texto": "xyzqw", "quantidade": 1}]}).responder(PHONE, "xyzqw")
    assert reply.texto.endswith("\n\nok ou não?") and " — 1 dz" in reply.texto
