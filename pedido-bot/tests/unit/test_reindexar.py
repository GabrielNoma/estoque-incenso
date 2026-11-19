"""Switching the embedding model and re-indexing the stored nicknames (spec US4)."""
from fakes import FakeEmbedder, InlineExecutor
from pedido import messages
from pedido.embeddings import EmbeddingFailed
from pedido.memoria import Memoria, reindexar

OGUM = 1010


def vec(*head):
    return list(head) + [0.0] * (1024 - len(head))


class FalhaEm(FakeEmbedder):
    def __init__(self, ruins, **kw):
        super().__init__(**kw)
        self.ruins = set(ruins)

    def embed(self, text):
        if text in self.ruins:
            raise EmbeddingFailed("falha simulada")
        return super().embed(text)


def aprender(store, texto, modelo="antigo", vetor=None, vezes=2):
    for _ in range(vezes):
        store.upsert_positivo(texto, OGUM, vetor if vetor is not None else vec(1.0), modelo)


def test_after_a_model_switch_exact_text_keeps_working_and_similarity_waits_for_the_reindex(store):
    aprender(store, "abre c felicidade")
    novo = FakeEmbedder({"abre c felicidade": [1.0, 0.0], "abre c da felicidade": [0.99, 0.1]}, model="novo")
    memoria = Memoria(store, novo, executor=InlineExecutor())
    assert memoria.buscar("abre c felicidade") == OGUM  # exact text: the model does not matter
    assert memoria.buscar("abre c da felicidade") is None  # vectors of the old model are never compared
    assert reindexar(store, novo) == (1, 0)
    assert memoria.buscar("abre c da felicidade") == OGUM  # now the similarity works with the new model


def test_reindexing_updates_every_nickname_and_deletes_nothing(store):
    for texto in ("a", "b", "c"):
        aprender(store, texto)
    antes = {r["id"] for r in store.list_apelidos()}
    assert reindexar(store, FakeEmbedder(model="novo")) == (3, 0)
    linhas = store.list_apelidos()
    assert {r["id"] for r in linhas} == antes and all(r["modelo"] == "novo" for r in linhas)
    assert all((r["positivos"], r["negativos"]) == (2, 0) for r in linhas)  # the signals are untouched


def test_a_failing_service_is_counted_and_the_successes_are_kept(store):
    for texto in ("bom", "ruim", "outro"):
        aprender(store, texto)
    assert reindexar(store, FalhaEm({"ruim"}, model="novo")) == (2, 1)
    por_texto = {r["texto_normalizado"]: r for r in store.list_apelidos()}
    assert por_texto["bom"]["modelo"] == "novo" and por_texto["outro"]["modelo"] == "novo"
    assert por_texto["ruim"]["modelo"] == "antigo"  # untouched, still there
