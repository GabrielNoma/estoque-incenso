"""Configuration: paths, the database URL and the default model name.

The API keys and the provider settings are read from the environment by `pedido.llm`; they are never
stored or shown.
"""
import os
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]

TEMPLATE_PATH = ROOT / "assets" / "PLANILHA_2024.xlsx"
ABBREVIATIONS_PATH = ROOT / "assets" / "abbreviations.json"

MODEL_NAME = os.environ.get("PEDIDO_MODEL", "claude-sonnet-5-5")


def database_url() -> str | None:
    return os.environ.get("DATABASE_URL")


def _number(name: str, default, kind=int):
    """A positive number from the environment; anything invalid falls back to the default."""
    try:
        value = kind(os.environ.get(name, ""))
    except ValueError:
        return default
    return value if value > 0 and value == value and value != float("inf") else default


def max_linhas() -> int:
    return _number("MAX_LINHAS", 50)


def max_texto_linha() -> int:
    return _number("MAX_TEXTO_LINHA", 120)


def max_mensagem() -> int:
    return _number("MAX_MENSAGEM", 2000)


def limite_msg_por_minuto() -> int:
    return _number("LIMITE_MSG_POR_MINUTO", 20)


def max_qtd_produto() -> int:
    return _number("MAX_QTD_PRODUTO", 1000)


def embed_dimensions() -> int:
    return _number("EMBED_DIMENSIONS", 1024)


def embed_timeout_seconds() -> int:
    return _number("EMBED_TIMEOUT_SECONDS", 5)


def embed_similarity() -> float:
    return _number("EMBED_SIMILARITY", 0.92, float)


def max_modelo_mb() -> int:
    return _number("MAX_MODELO_MB", 5)


def llm_timeout_seconds() -> int:
    """How long to wait for the language model (a big order takes about two minutes on a local model)."""
    return _number("LLM_TIMEOUT_SECONDS", 180)


# -- feature 006: hosting and cost limits ---------------------------------------------------------------
def _flag(name: str) -> bool:
    return os.environ.get(name, "").strip().lower() in ("1", "true", "sim", "yes")


def ambiente() -> str:
    """`producao` switches on the production rules; anything else is local use."""
    return "producao" if os.environ.get("ENVIRONMENT", "").strip().lower() == "producao" else "local"


def host() -> str:
    return "0.0.0.0" if ambiente() == "producao" else "127.0.0.1"


def porta() -> int:
    return _number("PORT", 10000) if ambiente() == "producao" else 8000


def llm_max_tokens() -> int:
    return _number("LLM_MAX_TOKENS", 4096)


def limite_diario_conversa() -> int:
    return _number("LIMITE_DIARIO_CONVERSA", 200)


def limite_req_por_chave() -> int:
    return _number("LIMITE_REQ_POR_CHAVE", 120)


def max_llm_concorrentes() -> int:
    return _number("MAX_LLM_CONCORRENTES", 4)


def espera_llm_segundos() -> int:
    return _number("ESPERA_LLM_SEGUNDOS", 20)


def max_corpo_mensagem_kb() -> int:
    return _number("MAX_CORPO_MENSAGEM_KB", 64)


def embed_send_dimensions() -> bool:
    return _flag("EMBED_SEND_DIMENSIONS")


def migrate_on_start() -> bool:
    return _flag("MIGRATE_ON_START")
