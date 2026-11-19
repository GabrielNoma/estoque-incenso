"""The embedding adapter: configured by environment, short timeout, never leaks the key."""
import pytest

from pedido.embeddings import EmbeddingFailed, build_embedder


def env(server, **extra):
    return {"EMBED_BASE_URL": server.base_url, "EMBED_MODEL": "fake-embed", "EMBED_API_KEY": "chave-secreta-1",
            "EMBED_DIMENSIONS": "8", **extra}


def test_not_configured_means_none():
    assert build_embedder({}) is None
    assert build_embedder({"EMBED_BASE_URL": "http://x/v1"}) is None
    assert build_embedder({"EMBED_MODEL": "m"}) is None


def test_embed_calls_the_server_with_the_model_and_the_key(openai_server):
    openai_server.embed_dimensions = 8
    embedder = build_embedder(env(openai_server))
    vector = embedder.embed("abre caminho")
    assert len(vector) == 8 and embedder.model == "fake-embed" and embedder.dimensions == 8
    request = openai_server.requests[-1]
    assert request["path"].endswith("/embeddings") and request["json"]["model"] == "fake-embed"
    assert request["authorization"] == "Bearer chave-secreta-1"


def test_a_slow_server_beyond_the_timeout_raises(openai_server):
    openai_server.embed_dimensions = 8
    openai_server.embed_delay = 3
    embedder = build_embedder(env(openai_server, EMBED_TIMEOUT_SECONDS="1"))
    with pytest.raises(EmbeddingFailed):
        embedder.embed("x")


def test_an_http_error_raises(openai_server):
    openai_server.fail_status = 500
    with pytest.raises(EmbeddingFailed):
        build_embedder(env(openai_server)).embed("x")


def test_a_vector_of_another_size_raises(openai_server):
    openai_server.embed_dimensions = 5
    with pytest.raises(EmbeddingFailed):
        build_embedder(env(openai_server)).embed("x")  # expects 8


def test_the_key_never_appears_in_the_representation(openai_server):
    embedder = build_embedder(env(openai_server))
    assert "chave-secreta-1" not in repr(embedder) and "chave-secreta-1" not in str(embedder)


# -- feature 006: hosted services may be asked for the vector size ----------------------------------------------
def test_the_configured_size_is_sent_as_dimensions_only_when_the_setting_is_on(openai_server):
    openai_server.embed_dimensions = 8
    build_embedder(env(openai_server, EMBED_SEND_DIMENSIONS="true")).embed("abre caminho")
    assert openai_server.requests[-1]["json"]["dimensions"] == 8
    build_embedder(env(openai_server)).embed("abre caminho")
    assert "dimensions" not in openai_server.requests[-1]["json"]
    build_embedder(env(openai_server, EMBED_SEND_DIMENSIONS="false")).embed("abre caminho")
    assert "dimensions" not in openai_server.requests[-1]["json"]


def test_a_vector_of_another_size_is_still_discarded_when_dimensions_are_sent(openai_server):
    openai_server.embed_dimensions = 5  # the service ignores the request and answers 5 numbers
    with pytest.raises(EmbeddingFailed):
        build_embedder(env(openai_server, EMBED_SEND_DIMENSIONS="true")).embed("x")
