"""Lista, ativa e desativa os apelidos aprendidos (contracts/script.md).

  uv run python scripts/apelidos.py                 # lista
  uv run python scripts/apelidos.py --desativar 12  # o apelido deixa de valer (nada é apagado)
  uv run python scripts/apelidos.py --ativar 12     # volta a valer, se a regra permitir
  uv run python scripts/apelidos.py --reindexar     # recalcula os vetores com o modelo de embeddings atual

Usa DATABASE_URL do ambiente.
"""
import argparse
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))

from pedido import messages  # noqa: E402
from pedido.catalog import load_catalog  # noqa: E402
from pedido.embeddings import build_embedder  # noqa: E402
from pedido.memoria import reindexar  # noqa: E402
from pedido.store import Store  # noqa: E402


FROM_ENV = object()


def main(argv: list[str] | None = None, url: str | None = None, embedder=FROM_ENV) -> int:
    parser = argparse.ArgumentParser(description="Apelidos aprendidos pelo bot.")
    group = parser.add_mutually_exclusive_group()
    group.add_argument("--desativar", type=int, metavar="ID", help="faz o apelido deixar de valer")
    group.add_argument("--ativar", type=int, metavar="ID", help="faz o apelido voltar a valer")
    group.add_argument("--reindexar", action="store_true",
                       help="recalcula o vetor de todos os apelidos com o modelo de embeddings atual (nada é apagado)")
    args = parser.parse_args(argv)
    url = url or os.environ.get("DATABASE_URL")
    if not url:
        print(messages.ERRO_BANCO_NAO_CONFIGURADO, file=sys.stderr)
        return 1
    store = Store(url)

    if args.reindexar:
        servico = build_embedder() if embedder is FROM_ENV else embedder
        if servico is None:
            print(messages.REINDEXAR_SEM_EMBEDDING)
            return 1
        feitos, falhas = reindexar(store, servico)
        print(messages.REINDEXAR_RESUMO.format(feitos=feitos, falhas=falhas))
        return 0

    for apelido_id, status, mensagem in ((args.desativar, "desativado", messages.APELIDO_DESATIVADO),
                                         (args.ativar, "ativo", messages.APELIDO_ATIVADO)):
        if apelido_id is not None:
            if not store.set_status(apelido_id, status):
                print(messages.APELIDO_NAO_ENCONTRADO)
                return 1
            print(mensagem.format(id=apelido_id))
            return 0

    rows = store.list_apelidos()
    if not rows:
        print(messages.APELIDOS_VAZIO)
        return 0
    ativo = store.modelo_ativo()  # the names come from the ACTIVE model (the seed file if there is none)
    nomes = {p.id: p.nome for p in (load_catalog(ativo["conteudo"]) if ativo else load_catalog())}

    def produto(r: dict) -> str:
        atual, guardado = nomes.get(r["produto_id"]), r.get("produto_nome")
        if guardado and atual != guardado:
            return f"{guardado} {messages.APELIDO_PRODUTO_MUDOU}"
        return atual or guardado or "?"
    print(" | ".join(messages.APELIDOS_CABECALHO))
    for r in rows:
        print(" | ".join(str(c) for c in (
            r["id"], r["texto_normalizado"], produto(r), r["positivos"], r["negativos"],
            r["status"], messages.SIM if r["aplica"] else messages.NAO)))
    return 0


if __name__ == "__main__":
    sys.exit(main())
