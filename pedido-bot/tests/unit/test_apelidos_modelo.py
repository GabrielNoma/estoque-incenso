"""Learned nicknames follow the model (spec US5): names recorded, disabled on change, never deleted."""
import pytest

from fakes import FakeEmbedder, InlineExecutor
from pedido.conversa import Conversa
from pedido.memoria import Memoria
from pedido.modelos import ModeloService

WORDING = "arruda velha"


@pytest.fixture
def setup(store, abbreviations, stub_chat, by_name):
    service = ModeloService(store, abbreviations)
    service.iniciar()
    ogum = by_name["Ogum"]

    def learn():
        memoria = Memoria(store, FakeEmbedder(), executor=InlineExecutor())
        bot = Conversa(store, service, stub_chat([{"linhas": [{"texto": WORDING, "quantidade": 1}]}] * 2),
                       abbreviations=abbreviations, memoria=memoria)
        for phone in ("1", "2"):
            bot.responder(phone, WORDING)
            bot.responder(phone, "ok")
        return bot

    return service, learn, ogum


def rows(store):
    return {r["texto_normalizado"]: r for r in store.list_apelidos()}


def test_a_learned_nickname_records_the_product_name(setup, store):
    service, learn, ogum = setup
    learn()
    row = rows(store)[WORDING]
    assert row["positivos"] == 2
    assert row["produto_nome"] == next(p.nome for p in service.atual().catalog if p.id == row["produto_id"])


def test_a_removed_product_disables_its_nicknames_and_deletes_nothing(setup, store, variante):
    service, learn, ogum = setup
    learn()
    nome = rows(store)[WORDING]["produto_nome"]
    resumo = service.importar(variante.sem_produto(nome), "sem.xlsx")
    assert resumo["apelidos_desativados"] == 1
    assert rows(store)[WORDING]["status"] == "desativado" and len(rows(store)) == 1


def test_a_renamed_product_disables_its_nicknames(setup, store, variante):
    service, learn, ogum = setup
    learn()
    nome = rows(store)[WORDING]["produto_nome"]
    assert service.importar(variante.renomeado(nome, nome + " Forte"), "renomeado.xlsx")["apelidos_desativados"] == 1
    assert rows(store)[WORDING]["status"] == "desativado"


def test_an_unrelated_change_keeps_the_nickname_active(setup, store, variante):
    service, learn, ogum = setup
    learn()
    assert service.importar(variante.com_produto_novo("Incenso Teste"), "novo.xlsx")["apelidos_desativados"] == 0
    assert rows(store)[WORDING]["status"] == "ativo"


def test_exporting_and_importing_the_same_file_keeps_every_nickname_active(setup, store, modelo_bytes):
    service, learn, ogum = setup
    learn()
    assert service.importar(service.atual().conteudo, "igual.xlsx")["apelidos_desativados"] == 0
    assert all(r["status"] == "ativo" for r in rows(store).values())


def test_nicknames_from_before_this_feature_get_their_name_at_startup(store, abbreviations, by_name):
    for _ in range(2):
        store.upsert_positivo("antigo", by_name["Ogum"].id)  # learned by 004: no name
    assert rows(store)["antigo"]["produto_nome"] is None
    ModeloService(store, abbreviations).iniciar()
    assert rows(store)["antigo"]["produto_nome"] == "Ogum" and rows(store)["antigo"]["status"] == "ativo"
