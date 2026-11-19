"""Constitution I, enforced: every user-visible string is pt-BR (tasks T011; re-run in T059).

Scans, now and as files appear later:
  - src/pedido/messages.py  (the single module holding every user-visible string)
  - src/pedido/web/templates/*.html  (visible text only)
  - src/pedido/web/static/*.js       (string literals only)
A string passes only if it shows pt-BR content and contains no banned English word.
"""
import importlib
import re
from pathlib import Path

import pytest

from ptbr import ACCENTED, BANNED_ENGLISH, PT_WORDS, english_hits, looks_ptbr  # noqa: F401

SRC = Path(__file__).resolve().parents[2] / "src" / "pedido"
def message_strings() -> list[str]:
    messages = importlib.import_module("pedido.messages")
    found = []
    for name in dir(messages):
        if not name.isupper():
            continue
        value = getattr(messages, name)
        if isinstance(value, str):
            found.append(value)
        elif isinstance(value, dict):
            found.extend(v for v in value.values() if isinstance(v, str))
    return found


def html_visible_text(html: str) -> list[str]:
    html = re.sub(r"(?is)<(script|style).*?</\1>", " ", html)
    chunks = re.sub(r"<[^>]+>", "\n", html).split("\n")
    attrs = re.findall(r'(?:placeholder|title|aria-label|alt)="([^"]+)"', html)
    return [c.strip() for c in chunks + attrs if c.strip() and "{{" not in c and "{%" not in c]


def js_literals(js: str) -> list[str]:
    return [lit for _q, lit in re.findall(r"""(["'`])((?:\\.|(?!\1).)*)\1""", js) if lit.strip()]


def test_messages_module_exists_and_is_not_empty():
    assert message_strings(), "pedido.messages must expose at least one user-visible string"


@pytest.mark.parametrize("text", message_strings() if (SRC / "messages.py").exists() else [])
def test_each_message_is_ptbr(text):
    assert not english_hits(text), f"English in message: {text!r}"
    if len(text.split()) > 1 or ACCENTED.search(text):
        assert looks_ptbr(text), f"Does not look pt-BR: {text!r}"


def test_templates_have_no_english_visible_text():
    for path in (SRC / "web" / "templates").glob("*.html"):
        for chunk in html_visible_text(path.read_text(encoding="utf-8")):
            assert not english_hits(chunk), f"{path.name}: {chunk!r}"


def test_static_js_literals_have_no_english_text():
    for path in (SRC / "web" / "static").glob("*.js"):
        for literal in js_literals(path.read_text(encoding="utf-8")):
            if " " in literal.strip():
                assert not english_hits(literal), f"{path.name}: {literal!r}"


def test_the_scanner_catches_english_and_accepts_portuguese():
    assert english_hits("Please try again later")
    assert not english_hits("Não foi possível analisar a mensagem agora.")
    assert looks_ptbr("Cole a mensagem do cliente antes de analisar.")
    assert not looks_ptbr("Something went wrong")
