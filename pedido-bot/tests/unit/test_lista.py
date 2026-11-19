"""Summing, Excel order and the plain list (Constitution III and IV)."""
import pytest

from pedido import lista


def test_aggregate_sums_the_same_product_and_follows_the_excel_order(by_name):
    later, first = by_name["Ogum"], by_name["Abre Caminho"]
    ordered = sorted([later, first], key=lambda p: (p.bloco, p.linha))
    result = lista.aggregate([(later, 1.0), (first, 0.5), (later, 2.0)])
    assert result == [(ordered[0], {later.id: 3.0, first.id: 0.5}[ordered[0].id]),
                      (ordered[1], {later.id: 3.0, first.id: 0.5}[ordered[1].id])]


def test_aggregate_drops_zero_and_negative_quantities(by_name):
    p = by_name["Ogum"]
    assert lista.aggregate([(p, 0.0), (p, -1.0)]) == []


def test_aggregate_of_nothing_is_empty():
    assert lista.aggregate([]) == []


@pytest.mark.parametrize("value, text", [(2, "2"), (2.0, "2"), (0.5, "0,5"), (2.25, "2,25"), (1.5, "1,5"), (12, "12")])
def test_formatar_quantidade_uses_a_comma_and_no_trailing_zeros(value, text):
    assert lista.formatar_quantidade(value) == text


def test_renderizar_is_exactly_the_list_and_the_closing_line(by_name):
    items = [(by_name["Abre Caminho"], 2.0), (by_name["Ogum"], 0.5)]
    items = lista.aggregate(items)
    text = lista.renderizar(items)
    lines = text.split("\n")
    assert lines[-2:] == ["", "ok ou não?"]
    assert all(l.endswith(" dz") and " — " in l for l in lines[:-2])
    assert len(lines) == len(items) + 2
    assert f"{items[0][0].nome} — {lista.formatar_quantidade(items[0][1])} dz" == lines[0]
