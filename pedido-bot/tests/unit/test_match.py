"""Closest match, exact first (Constitution IV)."""
import pytest

from pedido.match import Matcher


@pytest.fixture
def matcher(catalog, abbreviations):
    return Matcher(catalog, abbreviations=abbreviations)


@pytest.mark.parametrize("text, expected", [
    ("Abre Caminho", "Abre Caminho"),
    ("abre caminho", "Abre Caminho"),
    ("ABRE CAMINHO", "Abre Caminho"),
    ("abre c. da felicidade", "Abre C. da Felicidade"),
    ("abre caminho da felicidade", "Abre C. da Felicidade"),
    ("santa defesa santa paz e protecao", "S. Def.S.Paz e Proteção"),
    ("santo defesa saude paz e protecao", "S. Def.S.Paz e Proteção"),
    ("s def s paz e proteção", "S. Def.S.Paz e Proteção"),
    ("sete linhas", "7 Linhas"),
    ("7 linhas", "7 Linhas"),
])
def test_an_exact_wording_wins(matcher, text, expected):
    assert matcher.closest(text).nome == expected


def test_abre_caminho_never_goes_to_the_look_alike(matcher):
    assert matcher.closest("abre caminho").nome == "Abre Caminho"
    assert matcher.closest("abre c felicidade").nome == "Abre C. da Felicidade"


@pytest.mark.parametrize("text, expected", [
    ("abre camino", "Abre Caminho"),
    ("descarrego completto", "Descarrego Completo"),
])
def test_a_typo_goes_to_the_closest_product(matcher, text, expected):
    assert matcher.closest(text).nome == expected


def test_nonsense_still_returns_a_product(matcher, catalog):
    assert matcher.closest("xyzqw kkkk") in catalog


def test_a_tie_goes_to_the_first_product_in_excel_order(catalog, abbreviations):
    first, second = sorted(catalog, key=lambda p: (p.bloco, p.linha))[:2]
    twins = [second, first]  # the order of the list given to the matcher must not matter
    from dataclasses import replace
    a = replace(first, nome_normalizado="zzz", variantes=("zzz",))
    b = replace(second, nome_normalizado="zzz", variantes=("zzz",))
    assert Matcher([b, a], abbreviations=abbreviations).closest("zzy").id == a.id
    assert twins  # keeps the intent visible


def test_text_that_normalizes_to_nothing_returns_none(matcher):
    assert matcher.closest("") is None
    assert matcher.closest("  ...  ") is None


def test_there_is_no_review_machinery(matcher):
    result = matcher.closest("abre camino")
    assert not hasattr(result, "precisa_revisao")
    assert not hasattr(matcher, "match_one")


def test_the_runnable_maps_every_line(matcher):
    products = matcher.runnable().invoke(["abre caminho", "sete linhas"])
    assert [p.nome for p in products] == ["Abre Caminho", "7 Linhas"]


# -- learned nicknames (feature 004): exact -> nickname -> closest ------------------------------------------
def test_a_learned_nickname_beats_the_closest_product(catalog, abbreviations, by_name):
    ogum = by_name["Ogum"]
    baseline = Matcher(catalog, abbreviations=abbreviations).closest("arruda velha")
    assert baseline.id != ogum.id  # precondition: plain similarity prefers another product
    seen = []

    def apelidos(texto):
        seen.append(texto)
        return ogum.id if texto == "arruda velha" else None

    assert Matcher(catalog, abbreviations=abbreviations, apelidos=apelidos).closest("Arruda Velha!").id == ogum.id
    assert seen == ["arruda velha"]  # the lookup receives the normalized wording


def test_a_nickname_never_overrides_an_exact_wording(catalog, abbreviations, by_name):
    everything_is_ogum = Matcher(catalog, abbreviations=abbreviations, apelidos=lambda _t: by_name["Ogum"].id)
    assert everything_is_ogum.closest("abre caminho").nome == "Abre Caminho"
    assert everything_is_ogum.closest("sete linhas").nome == "7 Linhas"


@pytest.mark.parametrize("lookup", [lambda _t: None, lambda _t: 123456789,
                                    lambda _t: (_ for _ in ()).throw(RuntimeError("banco fora"))])
def test_a_missing_unknown_or_failing_nickname_falls_back_to_the_closest(catalog, abbreviations, lookup):
    plain = Matcher(catalog, abbreviations=abbreviations).closest("abre camino")
    assert Matcher(catalog, abbreviations=abbreviations, apelidos=lookup).closest("abre camino").id == plain.id


def test_exata_tells_whether_a_wording_is_an_exact_form_of_a_product(matcher, by_name):
    assert matcher.exata("Abre C. da Felicidade").nome == "Abre C. da Felicidade"
    assert matcher.exata("sete linhas").nome == "7 Linhas"
    assert matcher.exata("abre camino") is None
