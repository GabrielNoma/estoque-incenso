"""Shared fixtures. The LLM is always replaced by a stub (or the fake OpenAI-compatible server)."""
import json
import os
import uuid
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
FIXTURES = ROOT / "tests" / "fixtures"

ADMIN_URL = os.environ.get("PEDIDO_TEST_ADMIN_URL", "postgresql://pedido:pedido@localhost:5434/pedido")
TEST_DB_NAME = "pedido_test"
EMBED_DIMENSIONS = 1024
TABLES = ("apelidos", "pedidos", "catalog", "modelos", "uso_diario")


def load_json(*parts: str):
    return json.loads(FIXTURES.joinpath(*parts).read_text(encoding="utf-8"))


# -- the LLM stub -----------------------------------------------------------------------------------
class StubStructured:
    """What `chat.with_structured_output(Schema)` returns: invoke() yields the next canned response."""

    def __init__(self, schema, responses, prompts):
        self.schema = schema
        self._responses = responses
        self._prompts = prompts

    def invoke(self, prompt, *args, **kwargs):
        self._prompts.append(prompt)
        if not self._responses:
            raise AssertionError("StubChatModel: no canned response left")
        response = self._responses.pop(0)
        if isinstance(response, Exception):
            raise response
        return self.schema.model_validate(response)


class StubChatModel:
    """Stand-in for the chat model. `responses` are consumed in order, one per LLM call."""

    def __init__(self, responses=None):
        self.responses = list(responses or [])
        self.prompts: list = []
        self.calls = 0

    def with_structured_output(self, schema, **_kwargs):
        self.calls += 1
        return StubStructured(schema, self.responses, self.prompts)


@pytest.fixture
def stub_chat():
    """Factory: stub_chat([response, ...]) -> StubChatModel."""
    return StubChatModel


# -- the catalog and the regression messages --------------------------------------------------------------
@pytest.fixture(scope="session")
def abbreviations():
    from pedido.normalize import load_abbreviations

    return load_abbreviations()


@pytest.fixture(scope="session")
def catalog(abbreviations):
    from pedido.catalog import load_catalog

    return load_catalog(abbreviations=abbreviations)


@pytest.fixture
def by_name(catalog):
    return {p.nome: p for p in catalog}


@pytest.fixture(scope="session")
def regression():
    return load_json("mensagens", "expected.json")["mensagens"]


@pytest.fixture(scope="session")
def extractions():
    return load_json("llm_stubs", "extracoes.json")


@pytest.fixture(scope="session")
def canned():
    return load_json("llm_stubs", "respostas.json")


# -- the real Postgres (Docker) ---------------------------------------------------------------------------
def _admin():
    import psycopg

    return psycopg.connect(ADMIN_URL, autocommit=True, connect_timeout=5)


def _url_for(database: str) -> str:
    return ADMIN_URL.rsplit("/", 1)[0] + "/" + database


@pytest.fixture(scope="session")
def database_url():
    """URL of the test database. Fails loudly (never skips) when Postgres is not running."""
    import psycopg

    from pedido import db

    try:
        with _admin() as admin:
            exists = admin.execute("select 1 from pg_database where datname = %s", (TEST_DB_NAME,)).fetchone()
            if not exists:
                admin.execute(f'create database "{TEST_DB_NAME}"')
    except psycopg.OperationalError as error:
        pytest.fail("Postgres de teste inacessivel. Rode: docker compose up -d db  ("
                    + str(error).splitlines()[0] + ")")
    url = _url_for(TEST_DB_NAME)
    db.apply_schema(url, EMBED_DIMENSIONS)
    return url


@pytest.fixture
def clean_db(database_url):
    """Empty every table before the test (the schema stays)."""
    from pedido import db

    with db.connect(database_url) as conn:
        conn.execute("truncate " + ", ".join(f"pedido.{t}" for t in TABLES) + " restart identity cascade")
    return database_url


@pytest.fixture
def scratch_database_url():
    """Factory: scratch_database_url() -> URL of a throwaway empty database, dropped afterwards."""
    created = []

    def make() -> str:
        name = "pedido_scratch_" + uuid.uuid4().hex[:10]
        with _admin() as admin:
            admin.execute(f'create database "{name}"')
        created.append(name)
        return _url_for(name)

    yield make
    with _admin() as admin:
        for name in created:
            admin.execute(f'drop database if exists "{name}" with (force)')


@pytest.fixture
def store(clean_db):
    from pedido.store import Store

    return Store(clean_db)


@pytest.fixture
def openai_server():
    from fakes import FakeOpenAIServer

    with FakeOpenAIServer() as server:
        yield server


# -- the HTTP app ---------------------------------------------------------------------------------------
@pytest.fixture
def client(clean_db, stub_chat):
    """Factory: client(answer, ...) -> TestClient of an app on the test database and a stubbed model
    (no embedder unless one is passed, so the environment never leaks in)."""
    from fastapi.testclient import TestClient

    from pedido.web.app import create_app

    def make(*answers, chat_model=None, embedder=None, executor=None, api_keys=None):
        app = create_app(database_url=clean_db, chat_model=chat_model or stub_chat(list(answers)),
                         embedder=embedder, executor=executor, api_keys=api_keys)
        return TestClient(app)

    return make


@pytest.fixture
def embed_dimensions():
    return EMBED_DIMENSIONS


@pytest.fixture
def embedder():
    """Factory: embedder(table=None, fail=False) -> FakeEmbedder (1024 numbers, model "fake-embed")."""
    from fakes import FakeEmbedder

    return lambda table=None, fail=False: FakeEmbedder(table, EMBED_DIMENSIONS, fail=fail)


@pytest.fixture(scope="session")
def modelo_bytes():
    """The seed model (the original form) as bytes."""
    import modelos_helpers

    return modelos_helpers.seed_bytes()


@pytest.fixture
def variante():
    """The helpers that build variants of the model (new product, removed, renamed, invalid ones...)."""
    import modelos_helpers

    return modelos_helpers
