"""Settings of feature 006: production switches and the cost limits (contracts/configuration.md)."""
import pytest

from pedido import config


def test_local_defaults(monkeypatch):
    for name in ("ENVIRONMENT", "PORT"):
        monkeypatch.delenv(name, raising=False)
    assert (config.ambiente(), config.host(), config.porta()) == ("local", "127.0.0.1", 8000)


def test_production_listens_on_all_addresses_and_the_port_of_the_platform(monkeypatch):
    monkeypatch.setenv("ENVIRONMENT", "producao")
    monkeypatch.setenv("PORT", "9000")
    assert (config.ambiente(), config.host(), config.porta()) == ("producao", "0.0.0.0", 9000)
    monkeypatch.delenv("PORT")
    assert config.porta() == 10000
    monkeypatch.setenv("PORT", "abc")
    assert config.porta() == 10000


def test_the_port_is_ignored_outside_production(monkeypatch):
    monkeypatch.setenv("ENVIRONMENT", "desenvolvimento")
    monkeypatch.setenv("PORT", "9000")
    assert (config.host(), config.porta()) == ("127.0.0.1", 8000)


NUMBERS = {
    "llm_max_tokens": ("LLM_MAX_TOKENS", 4096),
    "limite_diario_conversa": ("LIMITE_DIARIO_CONVERSA", 200),
    "limite_req_por_chave": ("LIMITE_REQ_POR_CHAVE", 120),
    "max_llm_concorrentes": ("MAX_LLM_CONCORRENTES", 4),
    "espera_llm_segundos": ("ESPERA_LLM_SEGUNDOS", 20),
    "max_corpo_mensagem_kb": ("MAX_CORPO_MENSAGEM_KB", 64),
}


@pytest.mark.parametrize("name, spec", NUMBERS.items())
def test_defaults_overrides_and_invalid_values(monkeypatch, name, spec):
    var, default = spec
    monkeypatch.delenv(var, raising=False)
    assert getattr(config, name)() == default
    monkeypatch.setenv(var, "7")
    assert getattr(config, name)() == 7
    for bad in ("abc", "", "0", "-3"):
        monkeypatch.setenv(var, bad)
        assert getattr(config, name)() == default


@pytest.mark.parametrize("name, var", [("embed_send_dimensions", "EMBED_SEND_DIMENSIONS"),
                                       ("migrate_on_start", "MIGRATE_ON_START")])
def test_flags_are_off_by_default_and_read_at_call_time(monkeypatch, name, var):
    monkeypatch.delenv(var, raising=False)
    assert getattr(config, name)() is False
    for yes in ("true", "TRUE", "1", "sim"):
        monkeypatch.setenv(var, yes)
        assert getattr(config, name)() is True
    for no in ("false", "0", "", "talvez"):
        monkeypatch.setenv(var, no)
        assert getattr(config, name)() is False
