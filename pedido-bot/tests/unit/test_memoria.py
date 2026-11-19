"""The silent memory: lookup, learning and penalties, all failing softly (Constitution IV and VI)."""
import pytest

from fakes import FakeEmbedder, InlineExecutor
from pedido import config
from pedido.memoria import Memoria

OGUM, ARRUDA = 1010, 2011


def vec(*head):
    return list(head) + [0.0] * (1024 - len(head))


@pytest.fixture
def make(store):
    def build(embedder=None, **kwargs):
        return Memoria(store, embedder, executor=InlineExecutor(), **kwargs)
    return build


def test_buscar_finds_an_applying_nickname_by_exact_text_without_calling_the_embedder(store, make):
    embedder = FakeEmbedder()
    memoria = make(embedder)
    for _ in range(2):
        store.upsert_positivo("arruda velha", OGUM)
    assert memoria.buscar("arruda velha") == OGUM
    assert embedder.calls == []


def test_buscar_finds_a_similar_wording_above_the_threshold_only(store, make):
    embedder = FakeEmbedder({"abre c felicidade": [1.0, 0.0], "abre c da felicidade": [0.99, 0.1],
                             "ogum forte": [0.0, 1.0]})
    memoria = make(embedder)
    for _ in range(2):
        store.upsert_positivo("abre c felicidade", OGUM, embedder.embed("abre c felicidade"), embedder.model)
    assert memoria.buscar("abre c da felicidade") == OGUM
    assert memoria.buscar("ogum forte") is None  # similarity 0: below the threshold


def test_the_threshold_comes_from_the_configuration(store, make, monkeypatch):
    embedder = FakeEmbedder({"a": [1.0, 0.0], "b": [0.8, 0.6]})  # cosine 0.8
    memoria = make(embedder)
    for _ in range(2):
        store.upsert_positivo("a", OGUM, embedder.embed("a"), embedder.model)
    assert memoria.buscar("b") is None
    monkeypatch.setenv("EMBED_SIMILARITY", "0.7")
    assert memoria.buscar("b") == OGUM


def test_a_wording_of_another_model_is_not_compared(store, make):
    for _ in range(2):
        store.upsert_positivo("a", OGUM, vec(1.0), "outro-modelo")
    assert make(FakeEmbedder({"a2": [1.0]})).buscar("a2") is None


def test_a_failing_embedder_returns_none_and_is_skipped_for_the_rest_of_the_message(store, make):
    seed = FakeEmbedder()
    for _ in range(2):
        store.upsert_positivo("a", OGUM, seed.embed("a"), seed.model)
    embedder = FakeEmbedder(fail=True)
    memoria = make(embedder)
    memoria.nova_mensagem()
    assert memoria.buscar("x") is None and memoria.buscar("y") is None and memoria.buscar("z") is None
    assert embedder.calls == ["x"]  # one failure, no further calls in this message
    memoria.nova_mensagem()
    memoria.buscar("w")
    assert embedder.calls == ["x", "w"]  # the next message tries again


def test_no_embedder_call_when_no_nickname_exists_for_the_model(store, make):
    embedder = FakeEmbedder()
    assert make(embedder).buscar("qualquer coisa") is None
    assert embedder.calls == []


def test_a_database_error_never_raises(make):
    class Broken:
        def __getattr__(self, _name):
            def fail(*_a, **_k):
                raise RuntimeError("banco fora")
            return fail

    memoria = Memoria(Broken(), FakeEmbedder(), executor=InlineExecutor())
    assert memoria.buscar("x") is None
    memoria.aprender([("x", OGUM)])
    memoria.penalizar([("x", OGUM)])


def test_aprender_adds_a_positive_with_the_embedding_and_the_model(store, make):
    embedder = FakeEmbedder()
    make(embedder).aprender([("abre c felicidade", OGUM), ("arruda velha", ARRUDA)])
    rows = {r["texto_normalizado"]: r for r in store.list_apelidos()}
    assert rows["abre c felicidade"]["positivos"] == 1 and rows["abre c felicidade"]["modelo"] == "fake-embed"
    assert rows["arruda velha"]["produto_id"] == ARRUDA
    assert sorted(embedder.calls) == ["abre c felicidade", "arruda velha"]


def test_aprender_stores_the_row_without_embedding_when_the_embedder_fails(store, make):
    embedder = FakeEmbedder(fail=True)
    make(embedder).aprender([("a", OGUM), ("b", OGUM)])
    rows = store.list_apelidos()
    assert len(rows) == 2 and all(r["modelo"] is None and r["positivos"] == 1 for r in rows)
    assert embedder.calls == ["a"]  # after the first failure the batch stops asking


def test_a_wording_confirmed_once_does_not_apply_and_twice_does(store, make):
    memoria = make(FakeEmbedder())
    memoria.aprender([("apelido", OGUM)])
    assert memoria.buscar("apelido") is None
    memoria.aprender([("apelido", OGUM)])
    assert memoria.buscar("apelido") == OGUM


def test_penalizar_only_weakens_existing_wordings(store, make):
    memoria = make(FakeEmbedder())
    memoria.aprender([("apelido", OGUM)] * 1)
    memoria.aprender([("apelido", OGUM)])
    memoria.penalizar([("apelido", OGUM), ("inexistente", OGUM)])
    memoria.penalizar([("apelido", OGUM)])
    assert memoria.buscar("apelido") is None  # negatives reached positives
    assert {r["texto_normalizado"] for r in store.list_apelidos()} == {"apelido"}
    memoria.aprender([("apelido", OGUM)])
    assert memoria.buscar("apelido") == OGUM  # positives exceed negatives again


def test_agendar_runs_the_work_and_swallows_its_errors(store):
    ran = []
    memoria = Memoria(store, None, executor=InlineExecutor())
    memoria.agendar(lambda: ran.append(1))
    memoria.agendar(lambda: 1 / 0)
    assert ran == [1]


def test_the_default_executor_is_a_single_background_worker(store):
    import threading

    memoria = Memoria(store, None)
    done = threading.Event()
    memoria.agendar(done.set)
    assert done.wait(2)
