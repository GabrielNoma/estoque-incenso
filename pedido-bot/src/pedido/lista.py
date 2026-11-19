"""Summing, Excel order and the plain list the customer reads (Constitution III and IV)."""
from dataclasses import dataclass

from pedido import messages
from pedido.catalog import Product


@dataclass
class LinhaCasada:
    """One extracted line and the product it was matched to (before summing)."""
    texto: str
    quantidade: float
    produto: Product


@dataclass
class ResultadoPedido:
    """What the order chain returns: the summed items in Excel order, and the matched lines."""
    itens: list[tuple[Product, float]]
    linhas: list[LinhaCasada]


def aggregate(pairs: list[tuple[Product, float]]) -> list[tuple[Product, float]]:
    """Sum quantities by product, drop quantities <= 0, and order by the Excel position."""
    totals: dict[int, float] = {}
    products: dict[int, Product] = {}
    for product, quantity in pairs:
        products[product.id] = product
        totals[product.id] = totals.get(product.id, 0.0) + quantity
    ordered = sorted(products.values(), key=lambda p: (p.bloco, p.linha))
    return [(p, totals[p.id]) for p in ordered if totals[p.id] > 0]


def formatar_quantidade(value: float) -> str:
    """2 -> "2", 0.5 -> "0,5", 2.25 -> "2,25" (comma decimals, no trailing zeros)."""
    return f"{value:.2f}".rstrip("0").rstrip(".").replace(".", ",")


def renderizar(items: list[tuple[Product, float]]) -> str:
    """One line per product, a blank line and the closing question; nothing else."""
    lines = [f"{p.nome} — {formatar_quantidade(q)} dz" for p, q in items]
    return "\n".join(lines + ["", messages.PERGUNTA_CONFIRMACAO])
