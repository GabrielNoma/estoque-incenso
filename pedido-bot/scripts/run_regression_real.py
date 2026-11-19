"""Run the regression messages through the order chain and report the accuracy.

  uv run python scripts/run_regression_real.py            # offline: canned extractions (no network)
  uv run python scripts/run_regression_real.py --real     # the model from the environment (LLM_*)

Over tests/fixtures/mensagens/expected.json it prints:
  - the share of lines with an intended product that end on it (target >= 90%);
  - the exact-wording accuracy: every catalog wording must match its own product (target 100%).
The exit code is non-zero when either target is missed. Lines are compared in order.
"""
import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / "tests"))

from pedido.catalog import load_catalog  # noqa: E402
from pedido.chains import build_order_chain  # noqa: E402
from pedido.extract import extract  # noqa: E402
from pedido.match import Matcher  # noqa: E402
from pedido.normalize import load_abbreviations  # noqa: E402

FIXTURES = ROOT / "tests" / "fixtures"


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--real", action="store_true", help="use the model configured in the environment")
    args = parser.parse_args()
    catalog = load_catalog()
    matcher = Matcher(catalog, abbreviations=load_abbreviations())
    expected = json.loads((FIXTURES / "mensagens" / "expected.json").read_text(encoding="utf-8"))["mensagens"]
    canned = json.loads((FIXTURES / "llm_stubs" / "extracoes.json").read_text(encoding="utf-8"))
    if args.real:
        from pedido.llm import build_chat_model

        chat = build_chat_model()

    hits = total = 0
    for message in expected:
        text = (FIXTURES / "mensagens" / message["arquivo"]).read_text(encoding="utf-8")
        if args.real:
            lines = extract(text, chat)
        else:
            from conftest import StubChatModel

            lines = extract(text, StubChatModel([{"linhas": canned[message["arquivo"]]}]))
        wanted = [l for l in message["linhas"]]
        for index, line in enumerate(wanted):
            if not line["produto"]:
                continue
            total += 1
            got = matcher.closest(lines[index].texto) if index < len(lines) else None
            right = bool(got and got.nome == line["produto"])
            hits += right
            if not right:
                print(f"  ERRADO {message['arquivo']}: {line['texto']!r} -> {got and got.nome!r} "
                      f"(esperado {line['produto']!r})")
    exact_ok = all(matcher.closest(form).id == p.id for p in catalog for form in p.variantes)
    share = hits / total if total else 0.0
    print(f"linhas no produto pretendido: {hits}/{total} = {share:.0%} (meta >= 90%)")
    print(f"formas exatas corretas: {'100%' if exact_ok else 'FALHOU'} (meta 100%)")
    return 0 if share >= 0.90 and exact_ok else 1


if __name__ == "__main__":
    sys.exit(main())
