"""The memory inside the conversation: it changes the matched product, never what the customer sees."""
import pytest

from fakes import DeferredExecutor, FakeEmbedder, InlineExecutor
from pedido.conversa import Conversa
from pedido.match import Matcher
from pedido.memoria import Memoria
from pedido.normalize import normalize

OGUM = "Ogum"


def one(texto, quantidade=1):
    return {"linhas": [{"texto": texto, "quantidade": quantidade}]}


@pytest.fixture
def build(store, catalog, abbreviations, stub_chat):
    def make(*answers, embedder="default", executor=None, with_memory=True):
        memoria = None
        if with_memory:
            fake = FakeEmbedder() if embedder == "default" else embedder
            memoria = Memoria(store, fake, executor=executor or InlineExecutor())
        return Conversa(store, catalog, stub_chat(list(answers)), abbreviations=abbreviations, memoria=memoria)
    return make


def confirm(bot, phone, text):
    reply = bot.responder(phone, text)
    return reply, bot.responder(phone, "ok")


def test_two_confirmations_then_a_similar_wording_goes_to_the_confirmed_product(
        store, catalog, abbreviations, by_name, build):
    ogum = by_name[OGUM]
    wording, similar = "ogun", "arruda velha"
    assert Matcher(catalog, abbreviations=abbreviations).closest(similar).id != ogum.id  # plain similarity says another
    fake = FakeEmbedder({normalize(wording): [1.0, 0.0], normalize(similar): [0.99, 0.1]})
    bot = build(one(wording), one(similar), one(wording), one(similar), embedder=fake)
    confirm(bot, "1", wording)  # first confirmation
    assert OGUM not in bot.responder("2", similar).texto  # one confirmation is not enough
    confirm(bot, "3", wording)  # second confirmation of the same wording for the same product
    assert bot.responder("4", similar).texto == "Ogum — 1 dz\n\nok ou não?"


def test_an_exact_text_nickname_applies_even_with_the_embedder_down(store, catalog, abbreviations, by_name, build):
    ogum = by_name[OGUM]
    similar = "arruda velha"
    for _ in range(2):
        store.upsert_positivo(normalize(similar), ogum.id)
    bot = build(one(similar), embedder=FakeEmbedder(fail=True))
    assert bot.responder("1", similar).texto == "Ogum — 1 dz\n\nok ou não?"


def test_an_exact_wording_of_another_product_wins_over_a_nickname(store, by_name, build):
    for _ in range(3):
        store.upsert_positivo("abre caminho", by_name[OGUM].id)
    reply = build(one("abre caminho")).responder("1", "abre caminho")
    assert reply.texto == "Abre Caminho — 1 dz\n\nok ou não?"


SCRIPT = [one("ogum", 2), one("abre camino"), one("ogum", 2), one("abre camino"), one("arruda", 3)]


def run_script(bot):
    out = []
    for phone, text in (("1", "2 ogum"), ("1", "ok"), ("2", "abre camino"), ("2", "ok"), ("3", "2 ogum"),
                        ("3", "ok"), ("4", "abre camino"), ("4", "não"), ("5", "3 arruda")):
        reply = bot.responder(phone, text)
        out.append((reply.texto, reply.arquivo_nome is not None, reply.arquivo_bytes is not None))
    return out


def test_the_replies_are_byte_for_byte_those_of_a_bot_without_memory(build):
    with_memory = run_script(build(*SCRIPT))
    without = run_script(build(*SCRIPT, with_memory=False))
    assert with_memory == without


def test_the_memory_is_written_after_the_reply(store, build):
    executor = DeferredExecutor()
    bot = build(one("arruda velha"), executor=executor)
    bot.responder("1", "arruda velha")
    reply = bot.responder("1", "ok")
    assert reply.arquivo_bytes and store.list_apelidos() == []  # the reply left before anything was written
    executor.run()
    assert [r["positivos"] for r in store.list_apelidos()] == [1]


def test_exact_wordings_are_never_remembered(store, build):
    bot = build(one("abre caminho"))
    bot.responder("1", "abre caminho")
    bot.responder("1", "ok")
    assert store.list_apelidos() == []


@pytest.mark.parametrize("fail_embedder, broken_store", [(True, False), (False, True)])
def test_a_failing_memory_never_changes_the_reply_or_the_file(
        store, catalog, abbreviations, stub_chat, fail_embedder, broken_store):
    class Broken:
        def __getattr__(self, _name):
            def fail(*_a, **_k):
                raise RuntimeError("banco fora")
            return fail

    memoria = Memoria(Broken() if broken_store else store, FakeEmbedder(fail=fail_embedder),
                      executor=InlineExecutor())
    bot = Conversa(store, catalog, stub_chat([one("arruda velha")]), abbreviations=abbreviations, memoria=memoria)
    order = bot.responder("1", "arruda velha")
    done = bot.responder("1", "ok")
    assert order.texto.endswith("ok ou não?") and done.arquivo_bytes[:2] == b"PK"


def test_no_reply_ever_mentions_the_memory(store, build):
    bot = build(*SCRIPT)
    for text in ("2 ogum", "ok", "abre camino", "não", "3 arruda"):
        reply = bot.responder("1", text)
        for word in ("apelido", "memória", "memoria", "aprend"):
            assert word not in reply.texto.lower()
