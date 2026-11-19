"""The nickname memory in Postgres (data-model.md). Product ids follow the Excel order (block, row)."""
import pytest

from pedido.store import Store

OGUM, ARRUDA = 1010, 2011  # any two ids; ties are broken by the smaller id (earlier in the Excel)


def vec(*head):
    return list(head) + [0.0] * (1024 - len(head))


def learn(store, texto, produto, times=1, vector=None, modelo="m1"):
    for _ in range(times):
        store.upsert_positivo(texto, produto, vector, modelo if vector is not None else None)


def test_upsert_creates_then_increments_and_keeps_the_latest_embedding(store):
    learn(store, "abre c felicidade", OGUM, vector=vec(1.0))
    learn(store, "abre c felicidade", OGUM, vector=vec(0.0, 1.0))
    (row,) = store.list_apelidos()
    assert (row["texto_normalizado"], row["produto_id"], row["positivos"], row["negativos"]) == (
        "abre c felicidade", OGUM, 2, 0)
    assert row["modelo"] == "m1" and row["status"] == "ativo"


def test_a_row_without_embedding_is_allowed(store):
    learn(store, "x", OGUM, 2)
    (row,) = store.list_apelidos()
    assert row["modelo"] is None and row["positivos"] == 2


def test_penalizar_only_counts_existing_rows_and_never_creates_or_deletes(store):
    assert store.penalizar("nao existe", OGUM) is False
    assert store.list_apelidos() == []
    learn(store, "a", OGUM)
    assert store.penalizar("a", OGUM) is True
    assert store.penalizar("a", ARRUDA) is False
    (row,) = store.list_apelidos()
    assert (row["positivos"], row["negativos"]) == (1, 1)


@pytest.mark.parametrize("positivos, negativos, aplica", [
    (0, 0, False), (1, 0, False), (2, 0, True), (2, 1, True), (2, 2, False), (3, 2, True), (3, 3, False)])
def test_the_applies_rule_in_exact_lookup(store, positivos, negativos, aplica):
    learn(store, "apelido", OGUM, positivos)
    for _ in range(negativos):
        store.penalizar("apelido", OGUM)
    assert store.buscar_exato("apelido") == (OGUM if aplica else None)
    assert store.list_apelidos()[0]["aplica"] is aplica if positivos else True


def test_a_disabled_nickname_never_applies_and_can_be_enabled_again(store):
    learn(store, "a", OGUM, 2)
    (row,) = store.list_apelidos()
    assert store.set_status(row["id"], "desativado") is True
    assert store.buscar_exato("a") is None and store.list_apelidos()[0]["aplica"] is False
    assert store.set_status(row["id"], "ativo") is True
    assert store.buscar_exato("a") == OGUM
    assert store.set_status(999999, "ativo") is False
    with pytest.raises(ValueError):
        store.set_status(row["id"], "inventado")


def test_exact_lookup_picks_the_best_balance_then_the_earlier_product(store):
    learn(store, "mesmo", ARRUDA, 3)
    learn(store, "mesmo", OGUM, 3)
    assert store.buscar_exato("mesmo") == OGUM  # equal balance: the smaller id (earlier in the Excel)
    learn(store, "mesmo", ARRUDA, 1)
    assert store.buscar_exato("mesmo") == ARRUDA  # better balance wins


def test_similar_lookup_returns_the_best_applying_match_above_the_threshold(store):
    learn(store, "perto", OGUM, 2, vec(1.0, 0.0))
    learn(store, "longe", ARRUDA, 2, vec(0.0, 1.0))
    assert store.buscar_similar(vec(1.0, 0.1), "m1", 0.85) == OGUM
    assert store.buscar_similar(vec(0.7, 0.7), "m1", 0.85) is None  # similarity ~0.707 for both


def test_similar_lookup_ignores_other_models_null_embeddings_disabled_and_not_applying(store):
    learn(store, "outro modelo", OGUM, 2, vec(1.0), modelo="m2")
    learn(store, "sem vetor", OGUM, 2)
    learn(store, "uma vez", OGUM, 1, vec(1.0))
    learn(store, "desativado", OGUM, 2, vec(1.0))
    row = next(r for r in store.list_apelidos() if r["texto_normalizado"] == "desativado")
    store.set_status(row["id"], "desativado")
    learn(store, "negativo", OGUM, 2, vec(1.0))
    store.penalizar("negativo", OGUM)
    store.penalizar("negativo", OGUM)
    assert store.buscar_similar(vec(1.0), "m1", 0.85) is None


def test_tem_apelidos_tells_whether_a_similarity_search_could_find_anything(store):
    assert store.tem_apelidos("m1") is False
    learn(store, "a", OGUM, 1, vec(1.0))
    assert store.tem_apelidos("m1") is False  # not applying yet
    learn(store, "a", OGUM, 1, vec(1.0))
    assert store.tem_apelidos("m1") is True and store.tem_apelidos("m2") is False


def test_the_lines_of_an_order_round_trip(store):
    linhas = [{"texto": "abre c felicidade", "quantidade": 1.0, "produto_id": OGUM}]
    pedido_id = store.create_pedido("5511", "msg", [], "lista", linhas=linhas)
    assert store.get_pedido(pedido_id)["linhas"] == linhas
    assert store.get_pending("5511")["linhas"] == linhas
    assert store.get_pedido(store.create_pedido("5511", "outra", [], "l2"))["linhas"] == []


def test_a_new_store_sees_the_memory_like_after_a_restart(clean_db):
    learn(Store(clean_db), "a", OGUM, 2)
    assert Store(clean_db).buscar_exato("a") == OGUM
