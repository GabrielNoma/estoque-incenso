"""scripts/apelidos.py: list, disable and enable nicknames (contracts/script.md)."""
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "scripts"))

import apelidos  # noqa: E402

from pedido import messages  # noqa: E402
from ptbr import english_hits  # noqa: E402

@pytest.fixture
def ogum(by_name):
    return by_name["Ogum"].id


@pytest.fixture
def seeded(store, ogum):
    for _ in range(2):
        store.upsert_positivo("arruda velha", ogum)
    store.upsert_positivo("so uma vez", ogum)
    return store


def run(capsys, url, *args):
    code = apelidos.main(list(args), url)
    return code, capsys.readouterr().out


def test_the_list_shows_every_column_and_whether_it_applies(capsys, seeded, clean_db):
    code, out = run(capsys, clean_db)
    assert code == 0
    header, *rows = out.strip().splitlines()
    assert [c.strip() for c in header.split("|")] == list(messages.APELIDOS_CABECALHO)
    by_text = {r.split("|")[1].strip(): [c.strip() for c in r.split("|")] for r in rows}
    assert by_text["arruda velha"][2:] == ["Ogum", "2", "0", "ativo", "sim"]
    assert by_text["so uma vez"][2:] == ["Ogum", "1", "0", "ativo", "não"]


def test_an_empty_memory_says_so_in_portuguese(capsys, store, clean_db):
    assert run(capsys, clean_db) == (0, messages.APELIDOS_VAZIO + "\n")


def test_desativar_stops_it_applying_and_deletes_nothing(capsys, seeded, clean_db):
    row = next(r for r in seeded.list_apelidos() if r["texto_normalizado"] == "arruda velha")
    code, out = run(capsys, clean_db, "--desativar", str(row["id"]))
    assert code == 0 and out.strip() == messages.APELIDO_DESATIVADO.format(id=row["id"])
    assert seeded.buscar_exato("arruda velha") is None and len(seeded.list_apelidos()) == 2
    _, listing = run(capsys, clean_db)
    assert "desativado" in listing


def test_ativar_brings_it_back_when_the_rule_allows(capsys, seeded, clean_db, ogum):
    row = next(r for r in seeded.list_apelidos() if r["texto_normalizado"] == "arruda velha")
    run(capsys, clean_db, "--desativar", str(row["id"]))
    code, out = run(capsys, clean_db, "--ativar", str(row["id"]))
    assert code == 0 and out.strip() == messages.APELIDO_ATIVADO.format(id=row["id"])
    assert seeded.buscar_exato("arruda velha") == ogum


@pytest.mark.parametrize("flag", ["--ativar", "--desativar"])
def test_an_unknown_id_says_so_exits_1_and_changes_nothing(capsys, seeded, clean_db, flag):
    before = seeded.list_apelidos()
    code, out = run(capsys, clean_db, flag, "999999")
    assert code == 1 and out.strip() == messages.APELIDO_NAO_ENCONTRADO
    assert seeded.list_apelidos() == before


def test_all_the_output_is_portuguese(capsys, seeded, clean_db):
    _, out = run(capsys, clean_db)
    assert english_hits(out) == []
    assert messages.APELIDO_ATIVADO.startswith("Apelido") and not english_hits(messages.APELIDO_NAO_ENCONTRADO)


def test_the_list_notes_when_the_product_changed_in_the_model(capsys, store, clean_db, ogum, abbreviations):
    from pedido.modelos import ModeloService

    ModeloService(store, abbreviations).iniciar()
    for _ in range(2):
        store.upsert_positivo("velho apelido", ogum, produto_nome="Nome Antigo")
    _, out = run(capsys, clean_db)
    linha = next(l for l in out.splitlines() if "velho apelido" in l)
    assert "Nome Antigo" in linha and messages.APELIDO_PRODUTO_MUDOU in linha


# -- feature 006: --reindexar --------------------------------------------------------------------------------------
def test_reindexar_prints_the_totals_in_portuguese(capsys, seeded, clean_db):
    from fakes import FakeEmbedder

    code = apelidos.main(["--reindexar"], clean_db, embedder=FakeEmbedder(model="novo"))
    assert code == 0
    assert capsys.readouterr().out.strip() == messages.REINDEXAR_RESUMO.format(feitos=2, falhas=0)
    assert {r["modelo"] for r in seeded.list_apelidos()} == {"novo"}


def test_reindexar_without_an_embedder_refuses_in_portuguese(capsys, seeded, clean_db):
    code = apelidos.main(["--reindexar"], clean_db, embedder=None)
    assert code == 1 and capsys.readouterr().out.strip() == messages.REINDEXAR_SEM_EMBEDDING
