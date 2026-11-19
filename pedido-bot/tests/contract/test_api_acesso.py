"""Every route needs a key with the right scope (Constitution IX), through the real app."""
import logging

import pytest
from fastapi.routing import APIRoute

from pedido import messages
from pedido.acesso import REGRAS

CONVERSA = "c" * 40
MODELO = "m" * 40
TODAS = "t" * 40
API_KEYS = f"leitor:conversa:{CONVERSA},admin:modelo:{MODELO},estoque:conversa+modelo:{TODAS}"

ROTAS = [("POST", "/api/mensagem", "conversa", {"json": {"telefone": "1", "texto": "ogum"}}),
         ("GET", "/api/pedidos/1/planilha", "conversa", {}),
         ("GET", "/api/modelo", "modelo", {}),
         ("GET", "/api/modelo/info", "modelo", {}),
         ("POST", "/api/modelo", "modelo", {"content": b"x"})]


def chamar(http, metodo, caminho, extra, **headers):
    return http.request(metodo, caminho, headers=headers, **extra)


@pytest.mark.parametrize("metodo, caminho, escopo, extra", ROTAS)
def test_no_key_and_a_wrong_key_are_401_with_a_portuguese_error(client, metodo, caminho, escopo, extra):
    http = client(api_keys=API_KEYS)
    ausente = chamar(http, metodo, caminho, extra)
    assert ausente.status_code == 401
    assert ausente.json() == {"erro": "chave_ausente", "mensagem": messages.ERROS["chave_ausente"]}
    errada = chamar(http, metodo, caminho, extra, **{"X-API-Key": "e" * 40})
    assert errada.status_code == 401 and errada.json()["erro"] == "chave_invalida"


@pytest.mark.parametrize("metodo, caminho, escopo, extra", ROTAS)
def test_a_key_without_the_scope_is_403_and_the_right_scope_gets_through(client, metodo, caminho, escopo, extra):
    http = client(api_keys=API_KEYS)
    errada = CONVERSA if escopo == "modelo" else MODELO
    certa = MODELO if escopo == "modelo" else CONVERSA
    negado = chamar(http, metodo, caminho, extra, Authorization=f"Bearer {errada}")
    assert negado.status_code == 403
    assert negado.json() == {"erro": "sem_permissao", "mensagem": messages.ERROS["sem_permissao"]}
    passou = chamar(http, metodo, caminho, extra, Authorization=f"Bearer {certa}")
    assert passou.status_code not in (401, 403)


def test_a_key_with_both_scopes_and_the_other_header_work_as_before(client):
    http = client({"linhas": [{"texto": "ogum", "quantidade": 1}]}, api_keys=API_KEYS)
    resposta = http.post("/api/mensagem", json={"telefone": "1", "texto": "ogum"}, headers={"X-API-Key": TODAS})
    assert resposta.status_code == 200 and resposta.json()["resposta"].endswith("ok ou não?")
    assert http.get("/api/modelo/info", headers={"X-API-Key": TODAS}).status_code == 200


def test_the_health_check_needs_no_key_when_keys_are_configured(client):
    # /saude is built in the next phase; here only the rule table must already say it is public
    assert REGRAS[("GET", "/saude")] is None


def test_every_route_of_the_app_has_a_rule_and_its_dependency_enforces_it(client):
    http = client(api_keys=API_KEYS)
    locais = {"/", "/static"}
    vistos = set()
    for rota in http.app.routes:
        if not isinstance(rota, APIRoute) or rota.path in locais or rota.path in ("/openapi.json", "/docs", "/redoc",
                                                                                      "/docs/oauth2-redirect"):
            continue
        for metodo in rota.methods - {"HEAD", "OPTIONS"}:
            chave = (metodo, rota.path)
            assert chave in REGRAS, f"rota sem regra: {chave}"
            escopos = {getattr(d.call, "escopo", None) for d in rota.dependant.dependencies}
            assert (REGRAS[chave] in escopos) if REGRAS[chave] else not (escopos - {None}), chave
            vistos.add(chave)
    assert vistos and set(REGRAS) - vistos <= {("GET", "/saude")}  # every rule belongs to a real route


def test_no_cross_origin_permission_is_ever_sent(client):
    http = client(api_keys=API_KEYS)
    resposta = http.get("/api/modelo/info", headers={"Origin": "https://outro.exemplo", "X-API-Key": TODAS})
    assert "access-control-allow-origin" not in {k.lower() for k in resposta.headers}
    preflight = http.options("/api/mensagem", headers={"Origin": "https://outro.exemplo",
                                                       "Access-Control-Request-Method": "POST"})
    assert "access-control-allow-origin" not in {k.lower() for k in preflight.headers}


def test_the_121st_request_of_a_key_in_a_minute_gets_429(client, monkeypatch):
    monkeypatch.setenv("LIMITE_REQ_POR_CHAVE", "5")
    http = client(api_keys=API_KEYS)
    for _ in range(5):
        assert http.get("/api/modelo/info", headers={"X-API-Key": MODELO}).status_code == 200
    bloqueada = http.get("/api/modelo/info", headers={"X-API-Key": MODELO})
    assert bloqueada.status_code == 429
    assert bloqueada.json() == {"erro": "muitas_requisicoes", "mensagem": messages.ERROS["muitas_requisicoes"]}
    assert http.get("/api/modelo/info", headers={"X-API-Key": TODAS}).status_code == 200  # another key


def test_the_log_has_only_types_and_key_names(client, caplog):
    caplog.set_level(logging.DEBUG)
    http = client(api_keys=API_KEYS)
    http.get("/api/modelo/info")
    http.get("/api/modelo/info", headers={"X-API-Key": "e" * 40})
    http.get("/api/modelo/info", headers={"X-API-Key": CONVERSA})
    assert CONVERSA not in caplog.text and MODELO not in caplog.text and TODAS not in caplog.text
    assert "e" * 40 not in caplog.text
    assert "acesso=sem_permissao chave=leitor" in caplog.text


def test_without_keys_everything_works_and_a_warning_is_shown(client, caplog):
    caplog.set_level(logging.WARNING)
    http = client()
    assert http.get("/api/modelo/info").status_code == 200
    assert "API_KEYS" in caplog.text
