"""Fill the .xlsx copy of the order form with the approved quantities (research D1).

Only the quantity cells are written (columns A, E, I, M, Q of rows 4-46). Every formula, the
header and the layout are left exactly as they are; the original template is never modified.
"""
import io
import re
from pathlib import Path

import openpyxl

from pedido import config

QUANTITY_COLUMNS = {"A", "E", "I", "M", "Q"}
FIRST_ROW, LAST_ROW = 4, 46


class ProdutoAusente(Exception):
    """A product of the order is not in the model that is being filled."""


def quantities_for_export(finals: list[tuple[int, float]], catalog) -> dict[str, float]:
    """[(produto_id, quantidade), ...] -> {quantity cell: quantity}; repeated products are added."""
    cell_of = {p.id: p.celula_qtd for p in catalog}
    result: dict[str, float] = {}
    for produto_id, quantidade in finals:
        if produto_id not in cell_of:
            raise ProdutoAusente(str(produto_id))
        if quantidade:
            cell = cell_of[produto_id]
            result[cell] = result.get(cell, 0) + quantidade
    return result


def _check_quantity_cell(coord: str, merged_ranges) -> None:
    match = re.fullmatch(r"([A-Z]+)(\d+)", coord)
    if not match or match[1] not in QUANTITY_COLUMNS or not FIRST_ROW <= int(match[2]) <= LAST_ROW:
        raise ValueError(f"{coord} is not a quantity cell of the order form")
    if any(coord in rng for rng in merged_ranges):
        raise ValueError(f"{coord} belongs to a merged range and must not be written")


def fill_template(quantities: dict[str, float], template: Path | str | bytes | None = None) -> bytes:
    """Fill the model (a path, or the bytes of an .xlsx; default: the seed) with the quantities."""
    source = io.BytesIO(template) if isinstance(template, (bytes, bytearray)) else (template or config.TEMPLATE_PATH)
    workbook = openpyxl.load_workbook(source)
    sheet = workbook.worksheets[0]
    merged = list(sheet.merged_cells.ranges)
    for coord, quantidade in quantities.items():
        _check_quantity_cell(coord, merged)
        sheet[coord].value = quantidade
    workbook.calculation.fullCalcOnLoad = True  # Excel recomputes the price and total formulas
    buffer = io.BytesIO()
    workbook.save(buffer)
    return buffer.getvalue()
