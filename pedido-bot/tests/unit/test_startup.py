"""Startup validation: the tool refuses to start, in Portuguese (tasks T004)."""
import os
import subprocess
import sys
from pathlib import Path

import pytest

from pedido import messages
from pedido.db import StartupError
from pedido.startup import check_all, validate_environment

SRC = str(Path(__file__).resolve().parents[2] / "src")
GOOD = {"DATABASE_URL": "postgresql://pedido:pedido@localhost:5434/pedido"}


def refusal(env):
    with pytest.raises(StartupError) as error:
        validate_environment(env)
    return str(error.value)


def test_a_missing_database_url_is_refused():
    assert refusal({}) == messages.ERRO_BANCO_NAO_CONFIGURADO


def test_an_invalid_llm_provider_is_refused():
    assert refusal({**GOOD, "LLM_PROVIDER": "gpt"}) == messages.ERRO_LLM_PROVIDER_INVALIDO


@pytest.mark.parametrize("env", [
    GOOD,
    {**GOOD, "LLM_PROVIDER": "anthropic"},
    {**GOOD, "LLM_PROVIDER": "openai_compatible"},  # a missing key is NOT a startup error
    {**GOOD, "EMBED_BASE_URL": "http://x/v1"},       # the old embeddings variables are simply ignored
])
def test_valid_configurations_pass(env):
    assert validate_environment(env) is None


def test_an_unreachable_database_is_refused_by_check_all():
    with pytest.raises(StartupError) as error:
        check_all({"DATABASE_URL": "postgresql://pedido:pedido@127.0.0.1:1/pedido"})
    assert str(error.value) == messages.ERRO_BANCO_INACESSIVEL


def run_module(env_extra):
    env = {k: v for k, v in os.environ.items() if k not in ("DATABASE_URL", "ANTHROPIC_API_KEY")}
    env.update(env_extra, PYTHONPATH=SRC)
    return subprocess.run([sys.executable, "-m", "pedido"], env=env, capture_output=True, text=True, timeout=30)


def test_the_command_exits_with_code_1_and_the_portuguese_message_without_a_database_url():
    result = run_module({})
    assert result.returncode == 1
    assert messages.ERRO_BANCO_NAO_CONFIGURADO in result.stdout + result.stderr


def test_the_command_exits_with_code_1_when_the_database_is_unreachable():
    result = run_module({"DATABASE_URL": "postgresql://pedido:pedido@127.0.0.1:1/pedido"})
    assert result.returncode == 1
    assert messages.ERRO_BANCO_INACESSIVEL in result.stdout + result.stderr
