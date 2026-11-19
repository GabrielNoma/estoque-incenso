"""The documents a consumer or an operator needs (spec US6)."""
import re
from pathlib import Path

from pedido.acesso import REGRAS

DOCS = Path(__file__).resolve().parents[2] / "docs"

VARIAVEIS = ["ENVIRONMENT", "PORT", "API_KEYS", "DATABASE_URL", "MIGRATE_ON_START", "ANTHROPIC_API_KEY",
             "LLM_PROVIDER", "LLM_MODEL", "LLM_MAX_TOKENS", "LLM_TIMEOUT_SECONDS", "LIMITE_DIARIO_CONVERSA",
             "LIMITE_REQ_POR_CHAVE", "LIMITE_MSG_POR_MINUTO", "MAX_LLM_CONCORRENTES", "ESPERA_LLM_SEGUNDOS",
             "MAX_CORPO_MENSAGEM_KB", "MAX_MODELO_MB", "EMBED_BASE_URL", "EMBED_MODEL", "EMBED_API_KEY",
             "EMBED_DIMENSIONS", "EMBED_SEND_DIMENSIONS", "EMBED_SIMILARITY"]
ERROS = ["chave_ausente", "chave_invalida", "sem_permissao", "muitas_requisicoes", "corpo_grande",
         "modelo_invalido", "modelo_grande", "pedido_nao_encontrado", "pedido_nao_confirmado", "requisicao_invalida"]


def ler(nome):
    return (DOCS / nome).read_text(encoding="utf-8")


def test_the_contract_lists_every_route_with_its_scope_and_a_curl_example():
    contrato = ler("contrato-api.md")
    for (metodo, caminho), escopo in REGRAS.items():
        exemplo = caminho.replace("{pedido_id}", "12")
        assert f"{metodo} {caminho}" in contrato, (metodo, caminho)
        assert f"{exemplo}" in contrato, f"sem exemplo curl para {caminho}"
        if escopo:
            assert re.search(rf"{re.escape(caminho)}.*{escopo}", contrato, flags=re.S), (caminho, escopo)
    assert contrato.count("curl ") >= len(REGRAS)


def test_the_contract_lists_the_headers_scopes_and_every_error_code():
    contrato = ler("contrato-api.md")
    for item in ("Authorization: Bearer", "X-API-Key", "conversa", "modelo", "401", "403", "429", "413", *ERROS):
        assert item in contrato, item


def test_the_hosting_guide_has_every_variable_the_migration_step_the_health_check_and_a_checklist():
    guia = ler("producao-render.md")
    for variavel in VARIAVEIS:
        assert variavel in guia, variavel
    assert "python -m pedido.migrate" in guia and "/saude" in guia
    assert guia.count("- [ ]") >= 8


def test_the_stock_requirement_states_the_variables_the_header_and_the_scopes():
    requisito = ler("requisito-estoque.md")
    for item in ("PEDIDO_BOT_URL", "PEDIDO_BOT_API_KEY", "Authorization: Bearer", "conversa", "modelo"):
        assert item in requisito, item


def test_no_document_contains_a_real_key():
    for arquivo in DOCS.glob("*.md"):
        texto = arquivo.read_text(encoding="utf-8")
        assert not re.search(r"sk-ant-[A-Za-z0-9_-]{20,}|apikey_[A-Za-z0-9]{10,}", texto), arquivo.name
