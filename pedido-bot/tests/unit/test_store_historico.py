"""Listing the stored orders, newest first, with a cursor (feature: order history)."""
from pedido.store import Store


def criar(store, telefone, texto, estado=None, itens=None):
    pedido_id = store.create_pedido(telefone, texto, itens or [{"produto_id": 1, "nome": "Ogum", "quantidade": 2}],
                                    "Ogum — 2 dz\n\nok ou não?")
    if estado:
        store.set_estado(pedido_id, estado, "ok" if estado == "confirmado" else "não")
    return pedido_id


def test_it_lists_newest_first_with_every_field(store):
    a = criar(store, "111", "primeiro", "confirmado")
    b = criar(store, "222", "segundo")
    linhas = store.listar_historico(10)
    assert [l["id"] for l in linhas] == [b, a]
    campos = set(linhas[0])
    assert {"id", "telefone", "mensagem", "itens", "lista", "estado", "resposta", "criado_em", "respondido_em",
            "modelo_versao"} <= campos
    assert linhas[1]["estado"] == "confirmado" and linhas[1]["resposta"] == "ok"
    assert linhas[0]["estado"] == "aguardando" and linhas[0]["resposta"] is None


def test_the_cursor_and_the_limit_page_through_everything_without_repeats(store):
    ids = [criar(store, f"{i}", f"pedido {i}") for i in range(5)]
    visto, antes = [], None
    while True:
        pagina = store.listar_historico(2, antes=antes)
        visto += [l["id"] for l in pagina]
        if len(pagina) < 2:
            break
        antes = pagina[-1]["id"]
    assert visto == sorted(ids, reverse=True)


def test_it_filters_by_state(store):
    criar(store, "1", "a", "confirmado")
    criar(store, "2", "b", "recusado")
    criar(store, "3", "c", "confirmado")
    assert [l["mensagem"] for l in store.listar_historico(10, estado="confirmado")] == ["c", "a"]
    assert [l["mensagem"] for l in store.listar_historico(10, estado="recusado")] == ["b"]


def test_a_new_store_sees_the_same_history(clean_db):
    criar(Store(clean_db), "1", "a")
    assert len(Store(clean_db).listar_historico(10)) == 1
