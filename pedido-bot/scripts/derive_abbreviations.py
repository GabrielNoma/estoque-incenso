"""One-off helper: list the abbreviation fragments found in the catalog's product names.

Run: uv run python scripts/derive_abbreviations.py
It prints every fragment that came from a '.'-abbreviated token (e.g. "C." or "Def.do") with its
count and the products it appears in, so the expansions in assets/abbreviations.json can be reviewed.
"""
import collections
import re
import sys
from pathlib import Path

import openpyxl

TEMPLATE = Path(__file__).resolve().parent.parent / "assets" / "PLANILHA_2024.xlsx"
NAME_COLUMNS = (3, 7, 11, 15, 19)  # C, G, K, O, S
FIRST_ROW, LAST_ROW = 4, 46


def catalog_names(path: Path = TEMPLATE) -> list[str]:
    sheet = openpyxl.load_workbook(path).worksheets[0]
    names = []
    for row in range(FIRST_ROW, LAST_ROW + 1):
        for col in NAME_COLUMNS:
            value = sheet.cell(row, col).value
            if isinstance(value, str) and value.strip():
                names.append(value.strip())
    return names


def abbreviation_fragments(names: list[str]) -> dict[str, list[str]]:
    found: dict[str, list[str]] = collections.defaultdict(list)
    for name in names:
        for token in name.split():
            if "." in token:
                for fragment in filter(None, token.split(".")):
                    found[fragment.lower()].append(name)
    return found


if __name__ == "__main__":
    for fragment, products in sorted(abbreviation_fragments(catalog_names()).items()):
        print(f"{fragment!r:10} x{len(products)}  e.g. {products[0]!r}")
    sys.exit(0)
