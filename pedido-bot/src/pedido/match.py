"""Closest match, exact first (Constitution IV, research D4).

A written product name goes to:
  1. the product whose exact wording it equals (catalog name, abbreviation expansions or a full wording
     of an ambiguous abbreviation, such as "santa" for "S.");
  2. otherwise the product of a learned nickname (the injected `apelidos` lookup, feature 004; any
     failure there is ignored);
  3. otherwise the product with the highest similarity, whatever the score (there is no floor).
Ties go to the first product in the Excel order, so the result is deterministic.
"""
import logging

from langchain_core.runnables import RunnableLambda
from rapidfuzz import fuzz

from pedido.catalog import Product
from pedido.normalize import normalize


log = logging.getLogger("pedido.match")


class Matcher:
    def __init__(self, catalog: list[Product], abbreviations: dict[str, str] | None = None,
                 apelidos=None):
        """`apelidos(normalized text) -> product id | None` looks up learned nicknames."""
        self.abbreviations = abbreviations
        self._apelidos = apelidos
        self._by_id = {p.id: p for p in catalog}
        self._ordered = sorted(catalog, key=lambda p: (p.bloco, p.linha))
        self._exact = {form: p for p in reversed(self._ordered) for form in p.variantes}

    def exata(self, texto: str) -> Product | None:
        """The product whose exact wording this text is, or None."""
        return self._exact.get(normalize(texto, self.abbreviations))

    def _apelido(self, query: str) -> Product | None:
        if self._apelidos is None:
            return None
        try:
            return self._by_id.get(self._apelidos(query))
        except Exception as error:  # the memory must never break the matching
            log.warning("consulta de apelidos falhou: %s", type(error).__name__)
            return None

    def closest(self, texto: str) -> Product | None:
        query = normalize(texto, self.abbreviations)
        if not query:
            return None
        if query in self._exact:
            return self._exact[query]
        learned = self._apelido(query)
        if learned is not None:
            return learned
        best, best_score = None, -1.0
        for product in self._ordered:  # Excel order: the first of equal scores keeps the lead
            score = max(fuzz.token_sort_ratio(query, form) for form in product.variantes)
            if score > best_score:
                best, best_score = product, score
        return best

    def runnable(self) -> RunnableLambda:
        """list[str] -> list[Product | None], one product per written line."""
        return RunnableLambda(lambda texts: [self.closest(text) for text in texts])
