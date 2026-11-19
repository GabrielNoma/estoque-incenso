"""Models in Postgres: versions, one active, never deleted (data-model.md)."""
import pytest

from pedido.store import Store


def test_the_first_model_becomes_version_1_and_active(store):
    assert store.modelo_ativo() is None and store.versao_ativa() is None
    assert store.salvar_modelo("a.xlsx", b"conteudo-a", 10) == 1
    ativo = store.modelo_ativo()
    assert (ativo["versao"], ativo["arquivo"], ativo["conteudo"], ativo["produtos"]) == (1, "a.xlsx", b"conteudo-a", 10)
    assert store.versao_ativa() == 1


def test_a_new_model_becomes_the_active_one_and_nothing_is_deleted(store):
    store.salvar_modelo("a.xlsx", b"a", 1)
    assert store.salvar_modelo("b.xlsx", b"b", 2) == 2
    assert store.modelo_ativo()["conteudo"] == b"b"
    assert [(m["versao"], m["arquivo"], m["ativo"]) for m in store.listar_modelos()] == [
        (1, "a.xlsx", False), (2, "b.xlsx", True)]
    assert store.get_modelo(1)["conteudo"] == b"a"  # the previous file is intact
    assert store.get_modelo(99) is None
    assert "conteudo" not in store.listar_modelos()[0]


def test_a_failure_keeps_the_previous_active_model(store):
    store.salvar_modelo("a.xlsx", b"a", 1)
    with pytest.raises(Exception):
        store.salvar_modelo("b.xlsx", b"b", "não é número")  # fails after the old one was deactivated
    assert store.versao_ativa() == 1 and len(store.listar_modelos()) == 1


def test_a_new_store_sees_the_active_model_like_after_a_restart(clean_db):
    Store(clean_db).salvar_modelo("a.xlsx", b"a", 1)
    assert Store(clean_db).versao_ativa() == 1


def test_set_estado_records_the_model_version(store):
    pedido_id = store.create_pedido("5511", "m", [], "l")
    store.set_estado(pedido_id, "confirmado", "ok", modelo_versao=3)
    assert store.get_pedido(pedido_id)["modelo_versao"] == 3
    outro = store.create_pedido("5512", "m", [], "l")
    store.set_estado(outro, "recusado", "não")
    assert store.get_pedido(outro)["modelo_versao"] is None


def test_a_nickname_keeps_the_product_name(store):
    store.upsert_positivo("arruda velha", 1010, produto_nome="Ogum")
    store.upsert_positivo("arruda velha", 1010)  # a later confirmation without a name keeps the stored one
    assert store.list_apelidos()[0]["produto_nome"] == "Ogum"


def catalogo(*pares):
    from types import SimpleNamespace

    return [SimpleNamespace(id=i, nome=n) for i, n in pares]


def test_sincronizar_fills_names_and_disables_missing_or_renamed_products_without_deleting(store):
    for texto, pid, nome in (("igual", 1, "Ogum"), ("mudou", 2, "Arruda"), ("sumiu", 3, "Lavanda"), ("antigo", 1, None)):
        for _ in range(2):
            store.upsert_positivo(texto, pid, produto_nome=nome)
    desativados = store.sincronizar_apelidos(catalogo((1, "Ogum"), (2, "Arruda Pura")))
    rows = {r["texto_normalizado"]: r for r in store.list_apelidos()}
    assert desativados == 2 and len(rows) == 4
    assert rows["igual"]["status"] == "ativo" and rows["mudou"]["status"] == "desativado"
    assert rows["sumiu"]["status"] == "desativado"
    assert rows["antigo"]["status"] == "ativo" and rows["antigo"]["produto_nome"] == "Ogum"  # filled from the model


def test_sincronizar_disables_an_old_nickname_without_name_whose_product_is_gone(store):
    store.upsert_positivo("velho", 9)
    assert store.sincronizar_apelidos(catalogo((1, "Ogum"))) == 1
    assert store.list_apelidos()[0]["status"] == "desativado"
