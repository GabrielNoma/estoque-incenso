"""Negative answers weaken a nickname and never erase it (Constitution IV)."""
import pytest

from fakes import FakeEmbedder, InlineExecutor
from pedido.conversa import Conversa
from pedido.memoria import Memoria

WORDING = "arruda velha"  # plain similarity says Arruda; the nickname says Ogum


def one(texto, quantidade=1):
    return {"linhas": [{"texto": texto, "quantidade": quantidade}]}


@pytest.fixture
def setup(store, catalog, abbreviations, stub_chat, by_name):
    ogum = by_name["Ogum"]

    def build(*answers):
        memoria = Memoria(store, FakeEmbedder(), executor=InlineExecutor())
        return Conversa(store, catalog, stub_chat(list(answers)), abbreviations=abbreviations, memoria=memoria)

    for _ in range(2):
        store.upsert_positivo(WORDING, ogum.id)
    return build, ogum


def counts(store):
    (row,) = store.list_apelidos()
    return row["positivos"], row["negativos"], row["aplica"]


def test_nao_adds_a_negative_and_a_replacement_adds_another_until_it_stops_applying(setup, store):
    build, ogum = setup
    bot = build(one(WORDING), one(WORDING), one(WORDING), one(WORDING))
    assert "Ogum" in bot.responder("1", WORDING).texto  # matched through the nickname
    bot.responder("1", "não")
    assert counts(store) == (2, 1, True)  # weaker, still applies
    bot.responder("2", WORDING)
    bot.responder("2", WORDING)  # a replacement of the order above
    assert counts(store) == (2, 2, False)  # negatives reached positives: it stops applying
    assert "Ogum" not in bot.responder("3", WORDING).texto  # matching falls back to the closest product


def test_one_more_confirmation_makes_it_apply_again(setup, store):
    build, ogum = setup
    bot = build(one(WORDING), one(WORDING), one(WORDING), one(WORDING))
    bot.responder("1", WORDING)
    bot.responder("1", "não")
    bot.responder("2", WORDING)
    bot.responder("2", WORDING)  # replaces: second negative
    assert counts(store)[2] is False
    bot.responder("2", "ok")  # confirms the replacement (matched through the nickname before it stopped)
    assert counts(store) == (3, 2, True)
    assert "Ogum" in bot.responder("4", WORDING).texto


def test_nothing_is_ever_deleted(setup, store):
    build, _ogum = setup
    bot = build(one(WORDING), one(WORDING), one(WORDING))
    for phone in ("1", "2", "3"):
        bot.responder(phone, WORDING)
        bot.responder(phone, "não")
    # the third order no longer matched through the nickname (it stopped applying), so it is not penalized
    assert len(store.list_apelidos()) == 1 and counts(store)[:2] == (2, 2)


def test_only_the_lines_of_the_refused_order_are_penalized_and_no_wording_is_created(setup, store, by_name):
    build, ogum = setup
    other = by_name["Arruda"]
    for _ in range(2):
        store.upsert_positivo("outro apelido", other.id)
    bot = build({"linhas": [{"texto": WORDING, "quantidade": 1}, {"texto": "palavra nova xyz", "quantidade": 1}]})
    bot.responder("1", "pedido")
    bot.responder("1", "não")
    rows = {r["texto_normalizado"]: r for r in store.list_apelidos()}
    assert set(rows) == {WORDING, "outro apelido"}  # the refused order created nothing
    assert rows[WORDING]["negativos"] == 1 and rows["outro apelido"]["negativos"] == 0


def test_the_replies_are_not_affected(setup):
    build, _ogum = setup
    bot = build(one(WORDING), one(WORDING))
    first = bot.responder("1", WORDING)
    refusal = bot.responder("1", "não")
    assert first.texto.endswith("ok ou não?") and refusal.texto == "Pedido cancelado. Pode enviar o pedido novamente."
