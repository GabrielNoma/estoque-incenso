"""The order chain over every regression message: extract | match | aggregate."""
from pathlib import Path

import pytest

from pedido.chains import build_order_chain
from pedido.match import Matcher

MESSAGES = Path(__file__).resolve().parent.parent / "fixtures" / "mensagens"


@pytest.fixture
def run(catalog, abbreviations, extractions, stub_chat):
    matcher = Matcher(catalog, abbreviations=abbreviations)

    def go(arquivo):
        chat = stub_chat([{"linhas": extractions[arquivo]}])
        text = (MESSAGES / arquivo).read_text(encoding="utf-8")
        return build_order_chain(matcher, chat).invoke(text)

    return go


def test_the_result_is_in_excel_order_with_one_entry_per_product(run, regression):
    for message in regression:
        result = run(message["arquivo"]).itens
        keys = [(p.bloco, p.linha) for p, _q in result]
        assert keys == sorted(keys), message["arquivo"]
        assert len({p.id for p, _q in result}) == len(result), message["arquivo"]


def test_repeated_products_are_summed(catalog, abbreviations, stub_chat):
    matcher = Matcher(catalog, abbreviations=abbreviations)
    chat = stub_chat([{"linhas": [{"texto": "ogum", "quantidade": 1}, {"texto": "Ogum", "quantidade": 2},
                                  {"texto": "abre caminho", "quantidade": 0.5}]}])
    result = build_order_chain(matcher, chat).invoke("1 ogum, 2 Ogum, meia dz abre caminho")
    assert {p.nome: q for p, q in result.itens} == {"Ogum": 3.0, "Abre Caminho": 0.5}


def test_a_message_without_an_order_gives_an_empty_result(run):
    result = run("10_sem_pedido.txt")
    assert result.itens == [] and result.linhas == []


def test_at_least_90_percent_of_the_lines_end_on_the_intended_product(catalog, abbreviations, regression):
    matcher = Matcher(catalog, abbreviations=abbreviations)
    hits = total = 0
    misses = []
    for message in regression:
        for line in message["linhas"]:
            if not line["produto"]:
                continue
            total += 1
            product = matcher.closest(line["texto"])
            if product and product.nome == line["produto"]:
                hits += 1
            else:
                misses.append((message["arquivo"], line["texto"], line["produto"], product and product.nome))
    assert total >= 30
    assert hits / total >= 0.90, f"{hits}/{total}: {misses}"


def test_exact_wordings_are_always_right(catalog, abbreviations):
    matcher = Matcher(catalog, abbreviations=abbreviations)
    for product in catalog:
        for form in product.variantes:
            assert matcher.closest(form).id == product.id


def test_the_result_keeps_the_matched_lines_before_summing(catalog, abbreviations, stub_chat):
    matcher = Matcher(catalog, abbreviations=abbreviations)
    chat = stub_chat([{"linhas": [{"texto": "ogum", "quantidade": 1}, {"texto": "Ogum", "quantidade": 2}]}])
    result = build_order_chain(matcher, chat).invoke("1 ogum, 2 Ogum")
    assert [(l.texto, l.quantidade, l.produto.nome) for l in result.linhas] == [
        ("ogum", 1.0, "Ogum"), ("Ogum", 2.0, "Ogum")]
    assert [(p.nome, q) for p, q in result.itens] == [("Ogum", 3.0)]
