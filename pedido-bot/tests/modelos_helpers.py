"""Builds variants of the order-form model for tests, always from the seed file (never modifying it)."""
import io

import openpyxl
from openpyxl.cell.cell import MergedCell

from pedido import config
from pedido.catalog import FIRST_ROW, LAST_ROW, NAME_COLUMNS


def seed_bytes() -> bytes:
    return config.TEMPLATE_PATH.read_bytes()


def _abrir(conteudo: bytes | None = None):
    return openpyxl.load_workbook(io.BytesIO(conteudo or seed_bytes()))


def _salvar(workbook) -> bytes:
    buffer = io.BytesIO()
    workbook.save(buffer)
    return buffer.getvalue()


def _celulas(sheet):
    """(row, column, value) of every product-name cell, in the layout order."""
    for row in range(FIRST_ROW, LAST_ROW + 1):
        for column in NAME_COLUMNS:
            yield row, column, sheet.cell(row, column).value


def _livre(sheet):
    for row, column, value in _celulas(sheet):
        if value is None:
            return row, column
    raise AssertionError("o modelo de teste não tem célula livre")


def _celula_do(sheet, nome: str):
    for row, column, value in _celulas(sheet):
        if isinstance(value, str) and value.strip() == nome:
            return row, column
    raise AssertionError(f"produto {nome!r} não está no modelo")


def com_produto_novo(nome: str = "Incenso Teste", conteudo: bytes | None = None) -> bytes:
    workbook = _abrir(conteudo)
    sheet = workbook.worksheets[0]
    row, column = _livre(sheet)
    sheet.cell(row, column).value = nome
    return _salvar(workbook)


def sem_produto(nome: str, conteudo: bytes | None = None) -> bytes:
    workbook = _abrir(conteudo)
    sheet = workbook.worksheets[0]
    row, column = _celula_do(sheet, nome)
    sheet.cell(row, column).value = None
    return _salvar(workbook)


def renomeado(de: str, para: str, conteudo: bytes | None = None) -> bytes:
    workbook = _abrir(conteudo)
    sheet = workbook.worksheets[0]
    row, column = _celula_do(sheet, de)
    sheet.cell(row, column).value = para
    return _salvar(workbook)


def nome_repetido(nome: str = "Ogum") -> bytes:
    workbook = _abrir()
    sheet = workbook.worksheets[0]
    row, column = _livre(sheet)
    sheet.cell(row, column).value = nome
    return _salvar(workbook)


def celula_mesclada(nome: str = "Ogum") -> bytes:
    workbook = _abrir()
    sheet = workbook.worksheets[0]
    row, column = _celula_do(sheet, nome)
    quantidade = sheet.cell(row, column - 2).coordinate
    vizinha = sheet.cell(row, column - 1).coordinate
    sheet.merge_cells(f"{quantidade}:{vizinha}")
    return _salvar(workbook)


def sem_produtos() -> bytes:
    workbook = _abrir()
    sheet = workbook.worksheets[0]
    for row, column, value in _celulas(sheet):
        if value is not None and not isinstance(sheet.cell(row, column), MergedCell):
            sheet.cell(row, column).value = None
    return _salvar(workbook)


VAZIO = b""
XLS_ANTIGO = b"\xd0\xcf\x11\xe0\xa1\xb1\x1a\xe1" + b"\x00" * 512
LIXO = b"isto nao e uma planilha"
