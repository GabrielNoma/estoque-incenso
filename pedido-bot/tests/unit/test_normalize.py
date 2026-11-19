"""Text normalizer (research D4, tasks T012). Needs the reviewed assets/abbreviations.json."""
import pytest

from pedido.normalize import load_abbreviations, load_variants, normalize, normalize_variants


def test_lowercase_accents_and_punctuation():
    assert normalize("Iemanjá") == "iemanja"
    assert normalize("  SÃO   Jorge!  ") == "sao jorge"
    assert normalize("Combate  Inveja") == "combate inveja"


def test_period_is_replaced_by_space_so_glued_tokens_split():
    assert normalize("Nossa Sra.Des.dos Nos") == "nossa senhora desatadora dos nos"


def test_abbreviations_from_the_reviewed_list_are_expanded():
    assert normalize("Abre C. da Felicidade") == "abre caminho da felicidade"
    assert normalize("Abre T. os Caminhos") == "abre todos os caminhos"
    assert normalize("Def.do Preto Velho") == "defesa do preto velho"


def test_defumador_and_defesa_normalize_the_same():
    assert normalize("defumador do preto velho") == normalize("Def.do Preto Velho")


def test_abre_c_da_felicidade_equals_the_spelled_out_name():
    assert normalize("Abre C. da Felicidade") == normalize("abre caminho da felicidade")


def test_prefix_of_a_longer_name_is_not_equal():
    assert normalize("abre caminho") != normalize("abre caminho da felicidade")


def test_s_is_not_collapsed_into_one_word_because_it_has_several_meanings():
    assert normalize("S. Def.S.Paz e Proteção") == "s defesa s paz e protecao"


def test_numbers_are_kept():
    assert normalize("7 Linhas") == "7 linhas"


def test_is_idempotent():
    once = normalize("Nossa Sra.Des.dos Nos")
    assert normalize(once) == once


def test_explicit_abbreviation_mapping_overrides_the_file():
    assert normalize("abre c felicidade", {"c": "cavalo"}) == "abre cavalo felicidade"


def test_load_abbreviations_returns_the_expansions_map():
    mapping = load_abbreviations()
    assert mapping["c"] == "caminho" and mapping["def"] == "defesa"
    assert "s" not in mapping


# -- ambiguous abbreviations become every full wording (variants) --------------------------------
def test_load_variants_reads_the_reviewed_meanings_of_s():
    assert load_variants()["s"] == ["santo", "santa", "saude"]


def test_an_ambiguous_abbreviation_expands_into_every_full_wording():
    forms = normalize_variants("S. Def.S.Paz e Proteção")
    assert "santa defesa santo paz e protecao" in forms
    assert "santo defesa santa paz e protecao" in forms
    assert "saude defesa saude paz e protecao" in forms
    assert "s defesa s paz e protecao" in forms  # exactly as written on the form
    assert len(forms) == len(set(forms)) == 16   # (three meanings + as written) for each of the two S
    assert forms[0] == normalize("S. Def.S.Paz e Proteção")  # the canonical form comes first


def test_text_without_an_ambiguous_abbreviation_has_exactly_one_form():
    assert normalize_variants("Abre C. da Felicidade") == ["abre caminho da felicidade"]
    assert normalize_variants("Ogum") == ["ogum"]


def test_seven_is_also_written_as_sete():
    assert load_variants()["7"] == ["sete"]
    assert normalize_variants("7 Linhas") == ["7 linhas", "sete linhas"]
