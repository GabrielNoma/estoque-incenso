"""contracts/http-api.md: export, import and information of the model, through the app."""
import io
from urllib.parse import quote

import openpyxl
import pytest

from pedido import messages
from pedido.catalog import load_catalog

XLSX = "application/octet-stream"
ORDER = {"linhas": [{"texto": "incenso teste", "quantidade": 2}]}


def enviar(http, conteudo, nome="novo.xlsx"):
    return http.post("/api/modelo", content=conteudo, headers={"Content-Type": XLSX, "X-Nome-Arquivo": quote(nome)})


def conversa(http, texto, telefone="5511999990010"):
    return http.post("/api/mensagem", json={"telefone": telefone, "texto": texto}).json()


# -- US1: export ------------------------------------------------------------------------------------------
def test_the_model_is_downloaded_as_an_xlsx_attachment(client, modelo_bytes):
    resposta = client().get("/api/modelo")
    assert resposta.status_code == 200
    assert 'attachment; filename="modelo-pedido.xlsx"' in resposta.headers["content-disposition"]
    assert resposta.content == modelo_bytes
    sheet = openpyxl.load_workbook(io.BytesIO(resposta.content)).worksheets[0]
    formulas = [c for row in sheet.iter_rows() for c in row if isinstance(c.value, str) and c.value.startswith("=")]
    assert len(load_catalog(resposta.content)) == 167 and len(formulas) == 189


def test_after_an_import_the_export_is_the_new_model(client, variante):
    http = client()
    novo = variante.com_produto_novo()
    assert enviar(http, novo).status_code == 200
    assert http.get("/api/modelo").content == novo


# -- US2: import ------------------------------------------------------------------------------------------
def test_a_new_product_is_used_by_the_next_order_with_no_restart(client, variante):
    http = client(ORDER)
    novo = variante.com_produto_novo("Incenso Teste")
    resumo = enviar(http, novo, "novo.xlsx")
    assert resumo.status_code == 200
    assert resumo.json() == {"versao": 2, "arquivo": "novo.xlsx", "produtos": 168, "adicionados": ["Incenso Teste"],
                             "removidos": [], "renomeados": [], "apelidos_desativados": 0}
    assert conversa(http, "2 dz incenso teste")["resposta"] == "Incenso Teste — 2 dz\n\nok ou não?"
    pronto = conversa(http, "ok")
    arquivo = http.get(pronto["arquivo"]["url"]).content
    produto = next(p for p in load_catalog(novo) if p.nome == "Incenso Teste")
    assert openpyxl.load_workbook(io.BytesIO(arquivo)).worksheets[0][produto.celula_qtd].value == 2


def test_exporting_and_importing_the_same_file_reports_no_change(client):
    http = client()
    exportado = http.get("/api/modelo").content
    resumo = enviar(http, exportado).json()
    assert resumo["adicionados"] == resumo["removidos"] == resumo["renomeados"] == [] and resumo["versao"] == 2


def test_removed_and_renamed_products_are_listed(client, variante):
    resumo = enviar(client(), variante.renomeado("Arruda", "Arruda Pura", variante.sem_produto("Ogum"))).json()
    assert resumo["removidos"] == ["Ogum"] and resumo["renomeados"] == [{"de": "Arruda", "para": "Arruda Pura"}]


@pytest.mark.parametrize("nome, mensagem", [
    ("VAZIO", messages.MODELO_VAZIO),
    ("XLS_ANTIGO", messages.MODELO_XLS),
    ("LIXO", messages.MODELO_ILEGIVEL),
])
def test_an_unusable_file_is_refused_and_the_model_does_not_change(client, variante, nome, mensagem):
    http = client({"linhas": [{"texto": "ogum", "quantidade": 1}]})
    resposta = enviar(http, getattr(variante, nome))
    assert resposta.status_code == 422
    assert resposta.json() == {"erro": "modelo_invalido", "mensagem": mensagem}
    assert http.get("/api/modelo/info").json()["versao"] == 1
    assert conversa(http, "ogum")["resposta"] == "Ogum — 1 dz\n\nok ou não?"  # the old model still works


def test_structural_problems_are_refused_with_their_message(client, variante, by_name):
    http = client()
    casos = [(variante.sem_produtos(), messages.MODELO_SEM_PRODUTOS),
             (variante.nome_repetido("Ogum"), messages.MODELO_NOME_REPETIDO.format(nome="Ogum")),
             (variante.celula_mesclada("Ogum"), messages.MODELO_CELULA_MESCLADA.format(celula=by_name["Ogum"].celula_qtd))]
    for conteudo, mensagem in casos:
        resposta = enviar(http, conteudo)
        assert resposta.status_code == 422 and resposta.json()["mensagem"] == mensagem
    assert http.get("/api/modelo/info").json()["versao"] == 1


def test_a_file_above_the_limit_is_refused_with_413(client, monkeypatch):
    monkeypatch.setenv("MAX_MODELO_MB", "1")
    http = client()
    resposta = enviar(http, b"x" * (1024 * 1024 + 10))
    assert resposta.status_code == 413
    assert resposta.json() == {"erro": "modelo_grande", "mensagem": messages.MODELO_GRANDE.format(limite=1)}
    assert http.get("/api/modelo/info").json()["versao"] == 1


def test_every_previous_model_is_kept_and_the_file_name_is_stored(client, variante, modelo_bytes):
    http = client()
    enviar(http, variante.com_produto_novo(), "modelo novo.xlsx")
    enviar(http, modelo_bytes, "volta.xlsx")
    modelos = http.app.state.store.listar_modelos()
    assert [(m["versao"], m["arquivo"], m["ativo"]) for m in modelos] == [
        (1, "PLANILHA_2024.xlsx", False), (2, "modelo novo.xlsx", False), (3, "volta.xlsx", True)]


# -- US4: information -------------------------------------------------------------------------------------
def test_info_shows_the_active_model(client, variante):
    http = client()
    info = http.get("/api/modelo/info").json()
    assert (info["versao"], info["arquivo"], info["produtos"]) == (1, "PLANILHA_2024.xlsx", 167) and info["ativado_em"]
    enviar(http, variante.com_produto_novo(), "novo.xlsx")
    info = http.get("/api/modelo/info").json()
    assert (info["versao"], info["arquivo"], info["produtos"]) == (2, "novo.xlsx", 168)


# -- US3 through HTTP: a confirmed order is regenerated from the model it was filled with ---------------
def test_a_confirmed_order_is_regenerated_from_its_own_model_version(client, variante, by_name):
    http = client({"linhas": [{"texto": "ogum", "quantidade": 2}]})
    conversa(http, "2 dz ogum")
    arquivo = conversa(http, "ok")["arquivo"]["url"]
    antes = http.get(arquivo).content
    enviar(http, variante.sem_produto("Ogum"))  # the product leaves the model AFTER the order was confirmed
    depois = http.get(arquivo)
    assert depois.status_code == 200
    cell = by_name["Ogum"].celula_qtd
    assert openpyxl.load_workbook(io.BytesIO(depois.content)).worksheets[0][cell].value == 2
    assert openpyxl.load_workbook(io.BytesIO(antes)).worksheets[0][cell].value == 2
