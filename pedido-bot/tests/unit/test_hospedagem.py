"""Hosting: server arguments from the environment, the container recipe and the hosting example."""
import re
from pathlib import Path

from pedido import __main__ as principal

RAIZ = Path(__file__).resolve().parents[2]


def test_server_arguments_come_from_the_environment(monkeypatch):
    monkeypatch.setenv("ENVIRONMENT", "producao")
    monkeypatch.setenv("PORT", "10001")
    assert principal.argumentos_do_servidor() == {"host": "0.0.0.0", "port": 10001}
    monkeypatch.delenv("ENVIRONMENT")
    assert principal.argumentos_do_servidor() == {"host": "127.0.0.1", "port": 8000}


def test_the_dockerfile_runs_as_a_non_root_user_and_starts_the_app():
    docker = (RAIZ / "Dockerfile").read_text(encoding="utf-8")
    usuarios = re.findall(r"^USER\s+(\S+)", docker, flags=re.M)
    assert usuarios and usuarios[-1] not in ("root", "0")
    assert re.search(r'^CMD\s+\[.*"python".*"-m".*"pedido".*\]', docker, flags=re.M)
    assert ".env" not in re.sub(r"\.env\.example", "", docker)  # no secret file is ever copied
    assert "--no-dev" in docker and "--frozen" in docker


def test_the_dockerignore_keeps_secrets_and_junk_out_of_the_image():
    linhas = {l.strip() for l in (RAIZ / ".dockerignore").read_text(encoding="utf-8").splitlines()}
    for item in (".env", ".env.*", ".venv", "tests", "specs", ".specify", ".claude", "docs"):
        assert item in linhas, item


def test_the_hosting_example_names_the_health_check_the_migration_step_and_does_not_sync_secrets():
    exemplo = (RAIZ / "deploy" / "render.yaml.example").read_text(encoding="utf-8")
    assert "healthCheckPath: /saude" in exemplo
    assert "python -m pedido.migrate" in exemplo
    for segredo in ("ANTHROPIC_API_KEY", "DATABASE_URL", "API_KEYS", "EMBED_API_KEY"):
        trecho = exemplo.split(f"key: {segredo}", 1)[1].split("- key:", 1)[0]
        assert "sync: false" in trecho, segredo
    assert "ENVIRONMENT" in exemplo and "producao" in exemplo
    assert not re.search(r"sk-ant|apikey_", exemplo)


# -- CI/CD: one workflow file in the repository root, two jobs, the bot job deploys only from main ---------------
RAIZ_REPO = Path(__file__).resolve().parents[3]


def test_the_workflow_tests_the_bot_on_pull_requests_and_deploys_only_from_main():
    fluxo = (RAIZ_REPO / ".github" / "workflows" / "deploy.yml").read_text(encoding="utf-8")
    assert "pull_request" in fluxo and "pedido-bot/**" in fluxo and "estoque-incenso/**" in fluxo
    assert "pgvector/pgvector:pg16" in fluxo and "uv sync --frozen" in fluxo and "uv run pytest" in fluxo
    assert "docker build" in fluxo  # the container recipe is checked on every change of the bot
    assert "RENDER_DEPLOY_HOOK_URL_BOT" in fluxo and "RENDER_DEPLOY_HOOK_URL:" in fluxo
    assert "python -m pedido.migrate" in fluxo and "BOT_DATABASE_URL_MIGRACAO" in fluxo
    assert fluxo.count("github.ref == 'refs/heads/main'") >= 2  # deploy steps run only on pushes to main
    assert not re.search(r"sk-ant|apikey_|postgresql://[^\s$]*supabase", fluxo)


def test_the_deploy_script_retries_and_names_the_secret_when_it_is_missing():
    roteiro = (RAIZ_REPO / ".github" / "scripts" / "disparar-deploy-render.sh").read_text(encoding="utf-8")
    assert "NOME_SECRET" in roteiro and "MAX_TENTATIVAS" in roteiro and "429" in roteiro and "exit 1" in roteiro
