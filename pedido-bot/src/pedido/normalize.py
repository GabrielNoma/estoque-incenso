"""Text normalizer shared by the catalog, the matcher and the aliases (research D4).

lowercase -> strip accents -> punctuation (including ".") becomes a space -> collapse spaces ->
expand the catalog's abbreviations token by token. Applied to BOTH the customer's text and the
catalog names, so "Abre C. da Felicidade" and "abre caminho da felicidade" become identical.
"""
import itertools
import json
import re
import unicodedata
from functools import lru_cache
from pathlib import Path

from pedido import config


def load_abbreviations(path: Path | str | None = None) -> dict[str, str]:
    data = json.loads(Path(path or config.ABBREVIATIONS_PATH).read_text(encoding="utf-8"))
    return dict(data["expansoes"])


@lru_cache(maxsize=1)
def _default_abbreviations() -> dict[str, str]:
    return load_abbreviations()


def load_variants(path: Path | str | None = None) -> dict[str, list[str]]:
    """Abbreviations with SEVERAL possible meanings (e.g. "s" = santo | santa | saude)."""
    data = json.loads(Path(path or config.ABBREVIATIONS_PATH).read_text(encoding="utf-8"))
    return {token: list(meanings) for token, meanings in data.get("variantes", {}).items()}


@lru_cache(maxsize=1)
def _default_variants() -> dict[str, list[str]]:
    return load_variants()


def _tokens(text: str) -> list[str]:
    decomposed = unicodedata.normalize("NFKD", text)
    plain = "".join(ch for ch in decomposed if not unicodedata.combining(ch)).lower()
    return re.sub(r"[^\w\s]|_", " ", plain).split()


def normalize(text: str, abbreviations: dict[str, str] | None = None) -> str:
    mapping = _default_abbreviations() if abbreviations is None else abbreviations
    return " ".join(mapping.get(token, token) for token in _tokens(text))


def normalize_variants(text: str, abbreviations: dict[str, str] | None = None,
                       variants: dict[str, list[str]] | None = None) -> list[str]:
    """Every full wording a catalog name can have. An ambiguous abbreviation ("s") becomes each of its
    meanings, and also stays as written, in every combination. The first form is `normalize(text)`.
    Text without ambiguous abbreviations has exactly one form."""
    mapping = _default_abbreviations() if abbreviations is None else abbreviations
    options = _default_variants() if variants is None else variants
    choices = []
    for token in _tokens(text):
        base = mapping.get(token, token)
        choices.append([base] + [mapping.get(m, m) for m in options[token]] if token in options else [base])
    forms = (" ".join(parts) for parts in itertools.product(*choices))
    return list(dict.fromkeys(forms))  # distinct, first occurrence order
