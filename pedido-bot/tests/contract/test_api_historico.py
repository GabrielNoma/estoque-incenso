"""GET /api/pedidos: the order history for the stock system (scope `historico`)."""
import pytest

from pedido import messages

ITENS = [{"produto_id": 2028, "nome": "Ogum", "quantidade": 2.0}, {"produto_id": 1004, "nome": "Abre Caminho", "quantidade": 0.5}]


def semear(http, telefone, texto, estado=None):
    store = http.app.state.store
    pedido_id = store.create_pedido(telefone, texto, ITENS, "Abre Caminho — 0,5 dz\nOgum — 2 dz\n\nok ou não?")
    if estado:
        store.set_estado(pedido_id, estado, "ok" if estado == "confirmado" else "não")
    return pedido_id


def test_an_empty_history_is_an_empty_list(client):
    assert client().get("/api/pedidos").json() == {"pedidos": [], "proximo": None}


def test_each_order_shows_what_the_stock_screen_needs_and_hides_the_internal_ids(client):
    http = client()
    confirmado = semear(http, "5511999990000", "2 dz ogum e meia abre caminho", "confirmado")
    pendente = semear(http, "5511888880000", "outro pedido")
    pedidos = http.get("/api/pedidos").json()["pedidos"]
    assert [p["id"] for p in pedidos] == [pendente, confirmado]  # newest first
    ok = pedidos[1]
    assert ok["conversa"] == "5511999990000" and ok["mensagem"] == "2 dz ogum e meia abre caminho"
    assert ok["itens"] == [{"nome": "Ogum", "quantidade": 2.0}, {"nome": "Abre Caminho", "quantidade": 0.5}]
    assert ok["estado"] == "confirmado" and ok["resposta"] == "ok" and ok["lista"].endswith("ok ou não?")
    assert ok["criado_em"] and ok["respondido_em"]
    assert ok["arquivo"] == {"nome": f"pedido-{confirmado}.xlsx", "url": f"/api/pedidos/{confirmado}/planilha"}
    assert pedidos[0]["arquivo"] is None and pedidos[0]["estado"] == "aguardando" and pedidos[0]["resposta"] is None
    assert "produto_id" not in str(pedidos)  # the product ids of the model are not part of the contract


def test_only_confirmed_orders_offer_the_file(client):
    http = client()
    semear(http, "1", "x")          # becomes `substituido` when the next order of the same phone arrives
    semear(http, "1", "y")          # stays `aguardando`
    semear(http, "2", "z", "recusado")
    pedidos = http.get("/api/pedidos").json()["pedidos"]
    assert {p["estado"] for p in pedidos} == {"substituido", "aguardando", "recusado"}
    assert all(p["arquivo"] is None for p in pedidos)


def test_pagination_walks_the_whole_history_without_repeats(client):
    http = client()
    ids = [semear(http, str(i), f"pedido {i}") for i in range(5)]
    visto, antes = [], None
    for _ in range(10):
        resposta = http.get("/api/pedidos", params={"limite": 2, **({"antes": antes} if antes else {})}).json()
        visto += [p["id"] for p in resposta["pedidos"]]
        antes = resposta["proximo"]
        if antes is None:
            break
    assert visto == sorted(ids, reverse=True)


def test_the_state_filter(client):
    http = client()
    semear(http, "1", "a", "confirmado")
    semear(http, "2", "b", "recusado")
    pedidos = http.get("/api/pedidos", params={"estado": "recusado"}).json()["pedidos"]
    assert [p["mensagem"] for p in pedidos] == ["b"]


@pytest.mark.parametrize("params", [{"limite": 0}, {"limite": 201}, {"limite": "abc"}, {"estado": "inventado"},
                                    {"antes": "abc"}, {"antes": 0}])
def test_bad_parameters_are_422_in_portuguese(client, params):
    resposta = client().get("/api/pedidos", params=params)
    assert resposta.status_code == 422
    assert resposta.json() == {"erro": "requisicao_invalida", "mensagem": messages.ERRO_REQUISICAO_INVALIDA}


def test_the_default_limit_is_50(client):
    http = client()
    for i in range(55):
        semear(http, "1", f"p{i}")
    resposta = http.get("/api/pedidos").json()
    assert len(resposta["pedidos"]) == 50 and resposta["proximo"] == resposta["pedidos"][-1]["id"]
