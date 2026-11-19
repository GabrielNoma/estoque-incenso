"""Catalog loaded from the .xlsx copy of the order form (research D2, tasks T007)."""
import openpyxl
import pytest

from pedido import config

LABELS = {"P1": "Data:", "A2": "Razão Social:", "H2": "End.:", "A3": "Cidade:",
          "H3": "Estado:", "K3": "Prazo de Pagamento:", "P3": "Transp.:"}
HEADER_INPUTS = ["Q1", "D2", "I2", "D3", "I3", "M3", "Q3"]


@pytest.fixture(scope="module")
def sheet():
    return openpyxl.load_workbook(config.TEMPLATE_PATH).worksheets[0]


def test_loads_167_products_and_skips_footer_formulas(catalog):
    # 178 non-empty name-column cells minus 11 footer formulas in columns K and S
    assert len(catalog) == 167
    assert not any(p.nome.startswith("=") for p in catalog)


def test_abre_caminho_is_block_1_row_4(by_name):
    p = by_name["Abre Caminho"]
    assert (p.bloco, p.linha, p.celula_qtd) == (1, 4, "A4")


def test_alecrim_is_block_4_and_incensos(by_name):
    p = by_name["Alecrim"]
    assert (p.bloco, p.celula_qtd, p.categoria) == (4, "M4", "Incensos")


def test_categories_follow_blocks(catalog):
    for p in catalog:
        expected = "Defumadores" if p.bloco in (1, 2, 3) else "Incensos"
        assert p.categoria == expected, p.nome


def test_normalized_names_are_unique(catalog):
    names = [p.nome_normalizado for p in catalog]
    assert len(names) == len(set(names))


def test_ids_are_stable_per_block_and_row(by_name):
    assert by_name["Abre Caminho"].id == 1004


def test_quantity_cell_is_two_columns_left_of_name_cell(catalog, sheet):
    for p in catalog:
        qty = sheet[p.celula_qtd]
        name_cell = sheet.cell(row=qty.row, column=qty.column + 2)
        assert name_cell.value.strip() == p.nome, p.nome


def test_no_quantity_cell_is_merged(catalog, sheet):
    assert sheet.merged_cells.ranges  # the sheet really has merged cells (header and footer)
    for p in catalog:
        assert not any(p.celula_qtd in rng for rng in sheet.merged_cells.ranges), p.nome


def test_header_labels_and_empty_input_cells(sheet):
    for coord, text in LABELS.items():
        assert str(sheet[coord].value).strip() == text, coord
    for coord in HEADER_INPUTS:
        assert sheet[coord].value in (None, ""), coord


def test_template_keeps_all_189_formulas(sheet):
    formulas = [c for row in sheet.iter_rows() for c in row
                if isinstance(c.value, str) and c.value.startswith("=")]
    assert len(formulas) == 189


# -- exact wording variants of ambiguous abbreviations ------------------------------------------------
AMBIGUOUS = "S. Def.S.Paz e Proteção"


def test_the_ambiguous_product_keeps_its_canonical_name_and_gains_every_full_wording(by_name):
    p = by_name[AMBIGUOUS]
    assert p.nome_normalizado == "s defesa s paz e protecao"
    assert p.variantes[0] == p.nome_normalizado
    assert {"santa defesa santa paz e protecao", "santo defesa saude paz e protecao"} <= set(p.variantes)
    assert len(p.variantes) == 16


def test_every_other_product_has_exactly_one_exact_form_unless_it_starts_with_a_seven(catalog):
    assert all(p.variantes == (p.nome_normalizado,)
               for p in catalog if p.nome != AMBIGUOUS and not p.nome.startswith("7 "))


def test_no_two_products_share_an_exact_form(catalog):
    forms = [form for p in catalog for form in p.variantes]
    assert len(forms) == len(set(forms))


def test_the_seven_products_have_both_the_digit_and_the_written_form(by_name):
    for nome, written in (("7 Linhas", "sete linhas"), ("7 Forças", "sete forcas"), ("7 Giras", "sete giras")):
        assert by_name[nome].variantes == (by_name[nome].nome_normalizado, written)
