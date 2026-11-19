"""Filling the .xlsx copy of the order form (research D1, tasks T038)."""
import hashlib
import io
from pathlib import Path

import openpyxl
import pytest

from pedido import config
from pedido.export import fill_template, quantities_for_export

LABELS = {"P1": "Data:", "A2": "Razão Social:", "H2": "End.:", "A3": "Cidade:",
          "H3": "Estado:", "K3": "Prazo de Pagamento:", "P3": "Transp.:"}
HEADER_INPUTS = ["Q1", "D2", "I2", "D3", "I3", "M3", "Q3"]
ORIGINAL_XLS = Path(config.ROOT) / "assets" / "original" / "PLANILHA 2024.xls"


def digest(path) -> str:
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def open_result(data: bytes):
    return openpyxl.load_workbook(io.BytesIO(data))


def formulas(sheet) -> dict[str, str]:
    return {c.coordinate: c.value for row in sheet.iter_rows() for c in row
            if isinstance(c.value, str) and c.value.startswith("=")}


@pytest.fixture
def order(by_name):
    return {by_name["Abre Caminho"].celula_qtd: 2, by_name["Alecrim"].celula_qtd: 0.5,
            by_name["Ogum"].celula_qtd: 3}


def test_each_quantity_lands_in_the_products_cell(order):
    sheet = open_result(fill_template(order)).worksheets[0]
    for cell, quantity in order.items():
        assert sheet[cell].value == quantity


def test_only_the_quantity_cells_change(order):
    before = openpyxl.load_workbook(config.TEMPLATE_PATH).worksheets[0]
    after = open_result(fill_template(order)).worksheets[0]
    changed = {c.coordinate for row in after.iter_rows() for c in row
               if c.value != before[c.coordinate].value}
    assert changed == set(order)


def test_all_189_formulas_survive_unchanged(order):
    original = formulas(openpyxl.load_workbook(config.TEMPLATE_PATH).worksheets[0])
    filled = formulas(open_result(fill_template(order)).worksheets[0])
    assert len(original) == 189 and filled == original


def test_header_inputs_stay_empty_and_labels_unchanged(order):
    sheet = open_result(fill_template(order)).worksheets[0]
    for coord in HEADER_INPUTS:
        assert sheet[coord].value in (None, ""), coord
    for coord, text in LABELS.items():
        assert str(sheet[coord].value).strip() == text, coord


def test_layout_is_preserved(order):
    original = openpyxl.load_workbook(config.TEMPLATE_PATH)
    filled = open_result(fill_template(order))
    assert filled.sheetnames == original.sheetnames
    assert {str(r) for r in filled.worksheets[0].merged_cells.ranges} == {
        str(r) for r in original.worksheets[0].merged_cells.ranges}


def test_full_recalculation_is_requested_on_open(order):
    assert open_result(fill_template(order)).calculation.fullCalcOnLoad is True


def test_writing_into_a_merged_cell_is_refused():
    with pytest.raises(ValueError):
        fill_template({"E43": 1})  # E43:J43 is the "SUB-TOTAL DEFUMADORES" label


def test_unknown_cell_is_refused():
    with pytest.raises(ValueError):
        fill_template({"ZZ999": 1})


def test_result_is_a_real_xlsx(order):
    assert fill_template(order)[:2] == b"PK"


def test_quantities_for_export_maps_products_to_cells_and_sums_repeats(catalog, by_name):
    mapped = quantities_for_export([(by_name["Ogum"].id, 1), (by_name["Ogum"].id, 2)], catalog)
    assert mapped == {by_name["Ogum"].celula_qtd: 3}


def test_the_template_and_the_original_xls_are_never_modified(order):
    before = (digest(config.TEMPLATE_PATH), digest(ORIGINAL_XLS))
    fill_template(order)
    assert (digest(config.TEMPLATE_PATH), digest(ORIGINAL_XLS)) == before


# -- feature 005: the template may be bytes, and an unknown product is an error --------------------------------
def test_fill_template_accepts_the_model_as_bytes(modelo_bytes, by_name):
    cell = by_name["Ogum"].celula_qtd
    assert open_result(fill_template({cell: 2}, modelo_bytes)).worksheets[0][cell].value == 2


def test_a_new_product_of_a_new_model_gets_its_quantity_in_its_own_cell(variante):
    from pedido.catalog import load_catalog

    novo = variante.com_produto_novo("Incenso Teste")
    produto = next(p for p in load_catalog(novo) if p.nome == "Incenso Teste")
    sheet = open_result(fill_template({produto.celula_qtd: 3}, novo)).worksheets[0]
    assert sheet[produto.celula_qtd].value == 3


def test_an_unknown_product_is_refused_instead_of_dropped(catalog):
    from pedido.export import ProdutoAusente

    with pytest.raises(ProdutoAusente):
        quantities_for_export([(999999, 1)], catalog)
