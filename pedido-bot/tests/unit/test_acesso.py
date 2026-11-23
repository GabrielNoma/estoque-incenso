"""API keys: parsing, constant-time check, scopes, per-key rate limit (Constitution IX)."""
import logging

import pytest

from pedido import acesso, messages
from pedido.acesso import Acesso, ErroApi, carregar_chaves
from pedido.db import StartupError

K1 = "a" * 40
K2 = "b" * 40


def chaves():
    return carregar_chaves(f"estoque:conversa+modelo:{K1},whatsapp:conversa:{K2}")


def test_no_setting_means_no_keys():
    assert carregar_chaves(None) == [] and carregar_chaves("") == [] and carregar_chaves("  ") == []


def test_entries_are_parsed_into_name_scopes_and_secret():
    estoque, whatsapp = chaves()
    assert (estoque.nome, estoque.escopos, estoque.segredo) == ("estoque", frozenset({"conversa", "modelo"}), K1)
    assert (whatsapp.nome, whatsapp.escopos) == ("whatsapp", frozenset({"conversa"}))


@pytest.mark.parametrize("texto, mensagem", [
    ("sem-dois-pontos", messages.ERRO_CHAVE_MALFORMADA.format(n=1)),
    (f"a:conversa", messages.ERRO_CHAVE_MALFORMADA.format(n=1)),
    (f"ok:conversa:{K1},ruim:conversa:curta", messages.ERRO_CHAVE_MALFORMADA.format(n=2)),
    (f"a:conversa:{'x' * 31}", messages.ERRO_CHAVE_MALFORMADA.format(n=1)),
    (f"a::{K1}", messages.ERRO_CHAVE_MALFORMADA.format(n=1)),
    (f"a:voar:{K1}", messages.ERRO_ESCOPO_DESCONHECIDO.format(n=1, escopo="voar")),
    (f"a:conversa:{K1},a:modelo:{K2}", messages.ERRO_CHAVE_DUPLICADA.format(nome="a")),
])
def test_a_bad_entry_stops_the_start_without_showing_any_key(texto, mensagem):
    with pytest.raises(StartupError) as error:
        carregar_chaves(texto)
    assert str(error.value) == mensagem
    for segredo in (K1, K2, "curta", "x" * 31):
        assert segredo not in str(error.value)


def test_a_bearer_key_and_an_x_api_key_both_work_and_give_the_key_name():
    a = Acesso(chaves())
    assert a.autenticar({"authorization": f"Bearer {K1}"}, "modelo").nome == "estoque"
    assert a.autenticar({"x-api-key": K2}, "conversa").nome == "whatsapp"


def test_authorization_wins_over_x_api_key():
    a = Acesso(chaves())
    with pytest.raises(ErroApi) as error:
        a.autenticar({"authorization": "Bearer errada" + "z" * 30, "x-api-key": K1}, "conversa")
    assert (error.value.status, error.value.code) == (401, "chave_invalida")


def test_no_key_is_401_chave_ausente_and_a_wrong_key_is_401_chave_invalida():
    a = Acesso(chaves())
    with pytest.raises(ErroApi) as ausente:
        a.autenticar({}, "conversa")
    assert (ausente.value.status, ausente.value.code) == (401, "chave_ausente")
    with pytest.raises(ErroApi) as invalida:
        a.autenticar({"x-api-key": "c" * 40}, "conversa")
    assert (invalida.value.status, invalida.value.code) == (401, "chave_invalida")


def test_a_key_without_the_scope_is_403_sem_permissao():
    a = Acesso(chaves())
    with pytest.raises(ErroApi) as error:
        a.autenticar({"x-api-key": K2}, "modelo")  # whatsapp only has `conversa`
    assert (error.value.status, error.value.code) == (403, "sem_permissao")


def test_the_comparison_runs_against_every_key_even_after_a_match(monkeypatch):
    calls = []
    real = acesso.hmac.compare_digest
    monkeypatch.setattr(acesso.hmac, "compare_digest", lambda a, b: calls.append(1) or real(a, b))
    Acesso(chaves()).autenticar({"x-api-key": K1}, "conversa")  # matches the FIRST key
    assert len(calls) == 2


def test_access_is_off_when_there_are_no_keys():
    a = Acesso([])
    assert a.ativo is False and a.autenticar({}, "modelo") is None


def test_the_per_key_limit_blocks_the_next_request_and_spares_other_keys(monkeypatch):
    monkeypatch.setenv("LIMITE_REQ_POR_CHAVE", "3")
    relogio = [100.0]
    a = Acesso(chaves(), clock=lambda: relogio[0])
    for _ in range(3):
        a.autenticar({"x-api-key": K1}, "conversa")
    with pytest.raises(ErroApi) as error:
        a.autenticar({"x-api-key": K1}, "conversa")
    assert (error.value.status, error.value.code) == (429, "muitas_requisicoes")
    assert a.autenticar({"x-api-key": K2}, "conversa").nome == "whatsapp"
    relogio[0] += 61
    assert a.autenticar({"x-api-key": K1}, "conversa").nome == "estoque"


def test_logs_hold_only_the_type_and_the_key_name_never_the_key(caplog):
    caplog.set_level(logging.DEBUG)
    a = Acesso(chaves())
    for headers, escopo in (({}, "conversa"), ({"x-api-key": "c" * 40}, "conversa"), ({"x-api-key": K2}, "modelo")):
        with pytest.raises(ErroApi):
            a.autenticar(headers, escopo)
    assert K1 not in caplog.text and K2 not in caplog.text and "c" * 40 not in caplog.text
    assert "acesso=chave_ausente" in caplog.text and "acesso=chave_invalida" in caplog.text
    assert "acesso=sem_permissao chave=whatsapp" in caplog.text


def test_the_history_scope_exists_and_is_separate_from_the_others():
    chave = carregar_chaves(f"painel:historico:{K1},estoque:conversa+modelo+historico:{K2}")
    assert chave[0].escopos == frozenset({"historico"})
    assert chave[1].escopos == frozenset({"conversa", "modelo", "historico"})
    with pytest.raises(ErroApi) as error:  # the WhatsApp-style key (conversa only) cannot read the history
        Acesso(carregar_chaves(f"whatsapp:conversa:{K1}")).autenticar({"x-api-key": K1}, "historico")
    assert (error.value.status, error.value.code) == (403, "sem_permissao")
