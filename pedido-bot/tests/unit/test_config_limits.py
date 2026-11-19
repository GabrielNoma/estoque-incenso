"""Limits and embedding settings: documented defaults, read at call time (contracts/configuration.md)."""
import pytest

from pedido import config

DEFAULTS = {
    "max_linhas": ("MAX_LINHAS", 50),
    "max_texto_linha": ("MAX_TEXTO_LINHA", 120),
    "max_mensagem": ("MAX_MENSAGEM", 2000),
    "limite_msg_por_minuto": ("LIMITE_MSG_POR_MINUTO", 20),
    "max_qtd_produto": ("MAX_QTD_PRODUTO", 1000),
    "embed_dimensions": ("EMBED_DIMENSIONS", 1024),
    "embed_timeout_seconds": ("EMBED_TIMEOUT_SECONDS", 5),
    "embed_similarity": ("EMBED_SIMILARITY", 0.92),
    "max_modelo_mb": ("MAX_MODELO_MB", 5),
}


@pytest.mark.parametrize("name, spec", DEFAULTS.items())
def test_defaults(monkeypatch, name, spec):
    var, default = spec
    monkeypatch.delenv(var, raising=False)
    assert getattr(config, name)() == default


@pytest.mark.parametrize("name, spec", DEFAULTS.items())
def test_read_from_the_environment_at_call_time(monkeypatch, name, spec):
    var, default = spec
    monkeypatch.setenv(var, "7")
    assert getattr(config, name)() == 7


@pytest.mark.parametrize("name, spec", DEFAULTS.items())
@pytest.mark.parametrize("bad", ["abc", "", "-3", "0", "nan"])
def test_an_invalid_number_falls_back_to_the_default(monkeypatch, name, spec, bad):
    var, default = spec
    monkeypatch.setenv(var, bad)
    assert getattr(config, name)() == default


# -- feature 005 follow-up: the language model may be slow (a big order takes about two minutes locally) ----
def test_the_llm_timeout_defaults_to_180_seconds_and_is_configurable(monkeypatch):
    monkeypatch.delenv("LLM_TIMEOUT_SECONDS", raising=False)
    assert config.llm_timeout_seconds() == 180
    monkeypatch.setenv("LLM_TIMEOUT_SECONDS", "300")
    assert config.llm_timeout_seconds() == 300
    monkeypatch.setenv("LLM_TIMEOUT_SECONDS", "abc")
    assert config.llm_timeout_seconds() == 180
