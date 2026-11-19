"""GET /saude: the only public route; it never shows detail (Constitution IX)."""
import time

from pedido.store import Store

KEYS = "estoque:conversa+modelo:" + "k" * 40


def test_the_health_check_answers_ok_with_no_key_even_when_keys_are_configured(client):
    for http in (client(), client(api_keys=KEYS)):
        resposta = http.get("/saude")
        assert resposta.status_code == 200 and resposta.json() == {"status": "ok"}


def test_with_the_database_down_it_answers_503_with_no_detail(client, monkeypatch):
    http = client(api_keys=KEYS)

    def cair(self):
        raise RuntimeError("banco fora: postgresql://usuario:senha@host/db")

    monkeypatch.setattr(Store, "ping", cair)
    resposta = http.get("/saude")
    assert resposta.status_code == 503 and resposta.json() == {"status": "indisponivel"}
    assert "senha" not in resposta.text and "banco" not in resposta.text


def test_it_answers_in_under_a_second(client):
    http = client()
    inicio = time.monotonic()
    http.get("/saude")
    assert time.monotonic() - inicio < 1.0


def test_it_is_in_the_route_table_as_public():
    from pedido.acesso import REGRAS

    assert REGRAS[("GET", "/saude")] is None
