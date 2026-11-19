"""Startup validation: the tool refuses to start, in Portuguese, when the setup is wrong.

`validate_environment` checks the settings only; `check_all` also checks the database (and applies the
schema). Both raise `pedido.db.StartupError` carrying the message to show.
"""
import os

from pedido import config, db, messages
from pedido.acesso import carregar_chaves

LLM_PROVIDERS = {"anthropic", "openai_compatible"}


def validate_environment(env=None) -> None:
    env = os.environ if env is None else env
    if not env.get("DATABASE_URL"):
        raise db.StartupError(messages.ERRO_BANCO_NAO_CONFIGURADO)
    chaves = carregar_chaves(env.get("API_KEYS"))  # a bad entry stops the start (pt-BR, never shows a key)
    if config.ambiente() == "producao" and not chaves:
        raise db.StartupError(messages.ERRO_CHAVES_AUSENTES)
    if (env.get("LLM_PROVIDER", "anthropic").strip() or "anthropic") not in LLM_PROVIDERS:
        raise db.StartupError(messages.ERRO_LLM_PROVIDER_INVALIDO)


def check_all(env=None) -> None:
    env = os.environ if env is None else env
    validate_environment(env)
    db.check_database(env["DATABASE_URL"], config.embed_dimensions())
