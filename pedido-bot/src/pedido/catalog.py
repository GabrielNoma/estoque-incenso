"""The product catalog, read from the order form itself (research D2).

Names live in columns C, G, K, O, S (blocks 1-5), rows 4-46; the quantity cell is two columns to
the left. Cells whose text starts with "=" are footer formulas, not products.
"""
import io
from dataclasses import dataclass
from pathlib import Path

import openpyxl
from openpyxl.utils import get_column_letter

from pedido import config, messages
from pedido.normalize import normalize, normalize_variants

NAME_COLUMNS = (3, 7, 11, 15, 19)  # C, G, K, O, S -> blocks 1..5
FIRST_ROW, LAST_ROW = 4, 46
DEFUMADORES_BLOCKS = (1, 2, 3)  # blocks 4-5 are Incensos (confirmed by the footer formulas)


@dataclass(frozen=True)
class Product:
    id: int
    nome: str
    nome_normalizado: str
    categoria: str
    bloco: int
    linha: int
    celula_qtd: str
    variantes: tuple[str, ...] = ()  # every exact full wording (the canonical name comes first)



class NomeRepetido(ValueError):
    """Two products of the model have the same normalized name."""

    def __init__(self, forma: str, nome: str, anterior: str):
        super().__init__(f"Duplicate normalized product name {forma!r}: {anterior!r} and {nome!r}")
        self.nome = nome


class ModeloInvalido(Exception):
    """An uploaded model cannot be used; `mensagem` is the Portuguese sentence for the user."""

    def __init__(self, mensagem: str):
        super().__init__(mensagem)
        self.mensagem = mensagem


def _catalog_da_planilha(sheet, abbreviations, variants) -> list[Product]:
    products: list[Product] = []
    seen: dict[str, str] = {}
    for row in range(FIRST_ROW, LAST_ROW + 1):
        for block, column in enumerate(NAME_COLUMNS, start=1):
            value = sheet.cell(row, column).value
            if not isinstance(value, str) or not value.strip() or value.strip().startswith("="):
                continue
            nome = value.strip()
            normalizado = normalize(nome, abbreviations)
            formas = tuple(normalize_variants(nome, abbreviations, variants))
            for forma in formas:  # an exact wording must identify ONE product
                if forma in seen:
                    raise NomeRepetido(forma, nome, seen[forma])
                seen[forma] = nome
            products.append(Product(
                id=block * 1000 + row,
                nome=nome,
                nome_normalizado=normalizado,
                categoria="Defumadores" if block in DEFUMADORES_BLOCKS else "Incensos",
                bloco=block,
                linha=row,
                celula_qtd=f"{get_column_letter(column - 2)}{row}",
                variantes=formas,
            ))
    return products


def load_catalog(source: Path | str | bytes | None = None, abbreviations: dict[str, str] | None = None,
                 variants: dict[str, list[str]] | None = None) -> list[Product]:
    """The products of a model: a path (default: the seed file) or the bytes of an .xlsx."""
    fonte = io.BytesIO(source) if isinstance(source, (bytes, bytearray)) else (source or config.TEMPLATE_PATH)
    sheet = openpyxl.load_workbook(fonte).worksheets[0]
    return _catalog_da_planilha(sheet, abbreviations, variants)


def validar_modelo(conteudo: bytes, abbreviations: dict[str, str] | None = None,
                   variants: dict[str, list[str]] | None = None) -> list[Product]:
    """The catalog of an uploaded model, or `ModeloInvalido` with the sentence to show (research D2)."""
    if not conteudo:
        raise ModeloInvalido(messages.MODELO_VAZIO)
    if conteudo[:4] == b"\xd0\xcf\x11\xe0":  # the old binary .xls
        raise ModeloInvalido(messages.MODELO_XLS)
    try:
        sheet = openpyxl.load_workbook(io.BytesIO(conteudo)).worksheets[0]
    except Exception as error:  # not a zip, damaged, not a workbook...
        raise ModeloInvalido(messages.MODELO_ILEGIVEL) from error
    try:
        products = _catalog_da_planilha(sheet, abbreviations, variants)
    except NomeRepetido as error:
        raise ModeloInvalido(messages.MODELO_NOME_REPETIDO.format(nome=error.nome)) from error
    if not products:
        raise ModeloInvalido(messages.MODELO_SEM_PRODUTOS)
    merged = list(sheet.merged_cells.ranges)
    for product in products:
        if any(product.celula_qtd in cells for cells in merged):
            raise ModeloInvalido(messages.MODELO_CELULA_MESCLADA.format(celula=product.celula_qtd))
    return products
