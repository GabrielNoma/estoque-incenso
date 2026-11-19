"""contracts/http-api.md, with a real Postgres and a stubbed (or fake-server) model."""
import io

import openpyxl
import pytest

from pedido import messages
from pedido.llm import build_chat_model
from ptbr import looks_ptbr

PHONE = "5511999990005"
ORDER = {"linhas": [{"texto": "ogum", "quantidade": 2}, {"texto": "abre caminho", "quantidade": 0.5}]}


def send(client, texto, telefone=PHONE):
    return client.post("/api/mensagem", json={"telefone": telefone, "texto": texto})


def test_an_order_gets_exactly_the_list_and_no_file(client):
    http = client(ORDER)
    body = send(http, "2 dz ogum e meia abre caminho").json()
    assert body["arquivo"] is None
    lines = body["resposta"].split("\n")
    assert lines[-2:] == ["", "ok ou não?"]
    assert set(lines[:-2]) == {"Abre Caminho — 0,5 dz", "Ogum — 2 dz"}


def test_ok_returns_the_file_reference_and_the_file_is_regenerated_from_the_stored_items(client, by_name):
    http = client(ORDER)
    send(http, "pedido")
    body = send(http, "ok").json()
    assert body["resposta"] == messages.CONFIRMADO
    arquivo = body["arquivo"]
    assert arquivo["nome"].endswith(".xlsx") and arquivo["url"].startswith("/api/pedidos/")
    download = http.get(arquivo["url"])
    assert download.status_code == 200
    assert "attachment" in download.headers["content-disposition"] and arquivo["nome"] in download.headers["content-disposition"]
    sheet = openpyxl.load_workbook(io.BytesIO(download.content)).worksheets[0]
    assert sheet[by_name["Ogum"].celula_qtd].value == 2


def test_no_file_before_ok_and_none_for_a_second_ok(client):
    http = client(ORDER)
    assert send(http, "pedido").json()["arquivo"] is None
    assert send(http, "ok").json()["arquivo"] is not None
    again = send(http, "ok").json()
    assert again["arquivo"] is None and again["resposta"] == messages.ENVIE_PEDIDO


def test_phones_do_not_interfere(client):
    http = client({"linhas": [{"texto": "ogum"}]}, {"linhas": [{"texto": "abre caminho"}]})
    a = send(http, "ogum", "1").json()["resposta"]
    b = send(http, "abre caminho", "2").json()["resposta"]
    assert "Ogum" in a and "Ogum" not in b


def test_the_file_endpoint_errors_are_ptbr(client):
    http = client({"linhas": [{"texto": "ogum"}]})
    missing = http.get("/api/pedidos/999999/planilha")
    assert missing.status_code == 404
    assert missing.json() == {"erro": "pedido_nao_encontrado", "mensagem": messages.ERRO_PEDIDO_NAO_ENCONTRADO}
    send(http, "ogum")
    pedido_id = http.app.state.store.get_pending(PHONE)["id"]
    waiting = http.get(f"/api/pedidos/{pedido_id}/planilha")
    assert waiting.status_code == 409
    assert waiting.json()["erro"] == "pedido_nao_confirmado"


@pytest.mark.parametrize("payload", [{}, {"telefone": PHONE}, {"texto": "ogum"}, {"telefone": 1, "texto": "x"},
                                     {"telefone": PHONE, "texto": None}])
def test_missing_or_wrong_fields_give_422(client, payload):
    response = client().post("/api/mensagem", json=payload)
    assert response.status_code == 422
    assert response.json() == {"erro": "requisicao_invalida", "mensagem": messages.ERRO_REQUISICAO_INVALIDA}


def test_an_empty_text_is_a_normal_message(client):
    response = send(client(), "")
    assert response.status_code == 200 and response.json()["resposta"] == messages.SEM_ITENS


def test_the_home_page_is_portuguese_and_has_the_three_controls(client):
    html = client().get("/").text
    assert 'lang="pt-BR"' in html
    for label in (messages.PAGINA_TELEFONE, messages.PAGINA_CAMPO, messages.PAGINA_ENVIAR):
        assert label in html
    assert looks_ptbr(html)


def test_a_full_conversation_through_the_openai_compatible_adapter_never_leaks_the_key(client, openai_server):
    key = "chave-super-secreta-123"
    openai_server.chat_answers.append(ORDER)
    chat = build_chat_model({"LLM_PROVIDER": "openai_compatible", "LLM_BASE_URL": openai_server.base_url,
                             "LLM_MODEL": "fake-chat", "LLM_API_KEY": key})
    http = client(chat_model=chat)
    order = send(http, "2 dz ogum e meia abre caminho")
    confirmed = send(http, "ok")
    assert order.json()["resposta"].endswith("ok ou não?") and confirmed.json()["arquivo"]
    assert openai_server.requests and openai_server.requests[0]["authorization"] == f"Bearer {key}"
    blob = order.text + confirmed.text + http.get("/openapi.json").text + http.get("/").text
    blob += repr(http.app.state.store.list_pedidos())
    assert key not in blob


# -- feature 006: the message body limit (the model upload keeps its own) -----------------------------------------
def test_a_message_body_above_the_limit_gets_413_before_the_model_is_called(client, monkeypatch, stub_chat):
    monkeypatch.setenv("MAX_CORPO_MENSAGEM_KB", "1")
    chat = stub_chat([])
    http = client(chat_model=chat)
    grande = http.post("/api/mensagem", json={"telefone": PHONE, "texto": "x" * 2000})
    assert grande.status_code == 413
    assert grande.json() == {"erro": "corpo_grande", "mensagem": messages.ERROS["corpo_grande"]}
    assert chat.calls == 0


def test_a_small_message_still_works_and_the_model_upload_has_its_own_limit(client, monkeypatch):
    monkeypatch.setenv("MAX_CORPO_MENSAGEM_KB", "1")
    http = client(ORDER)
    assert http.post("/api/mensagem", json={"telefone": PHONE, "texto": "2 dz ogum"}).status_code == 200
    resposta = http.post("/api/modelo", content=b"x" * 100_000, headers={"Content-Type": "application/octet-stream"})
    assert resposta.status_code == 422  # reached the model validation: not cut by the message limit
