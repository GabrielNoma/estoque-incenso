"""The fake OpenAI-compatible chat server used to test the LLM adapters (tasks T007)."""
import httpx
import pytest

from fakes import FakeOpenAIServer


def test_the_server_records_requests_and_answers_chat_with_json_content():
    with FakeOpenAIServer() as server:
        server.chat_answers.append({"linhas": []})
        reply = httpx.post(f"{server.base_url}/chat/completions", headers={"Authorization": "Bearer chave-x"},
                           json={"model": "m", "messages": [{"role": "user", "content": "oi"}],
                                 "response_format": {"type": "json_schema",
                                                     "json_schema": {"name": "x", "schema": {}}}})
        assert reply.json()["choices"][0]["message"]["content"] == '{"linhas": []}'
        (seen,) = server.requests
        assert seen["path"] == "/v1/chat/completions" and seen["authorization"] == "Bearer chave-x"
        assert seen["json"]["model"] == "m"


def test_the_server_answers_with_a_tool_call_when_tools_are_sent():
    with FakeOpenAIServer() as server:
        server.chat_answers.append({"linhas": []})
        reply = httpx.post(f"{server.base_url}/chat/completions", json={
            "model": "m", "messages": [{"role": "user", "content": "oi"}],
            "tools": [{"type": "function", "function": {"name": "ExtracaoPedido", "parameters": {}}}]})
        call = reply.json()["choices"][0]["message"]["tool_calls"][0]
        assert call["function"]["name"] == "ExtracaoPedido" and call["function"]["arguments"] == '{"linhas": []}'


def test_the_server_can_answer_through_a_responder_that_sees_the_request():
    with FakeOpenAIServer() as server:
        server.chat_responder = lambda body: {"eco": body["messages"][0]["content"]}
        reply = httpx.post(f"{server.base_url}/chat/completions", json={
            "model": "m", "messages": [{"role": "user", "content": "ola"}]})
        assert reply.json()["choices"][0]["message"]["content"] == '{"eco": "ola"}'


def test_the_server_can_use_a_fixed_port():
    with FakeOpenAIServer(port=8791) as server:
        assert server.base_url == "http://127.0.0.1:8791/v1"


def test_the_server_can_fail_and_stops_after_the_with_block():
    with FakeOpenAIServer() as server:
        server.fail_status = 500
        failed = httpx.post(f"{server.base_url}/chat/completions", json={"model": "m", "messages": []})
        assert failed.status_code == 500
        url = server.base_url
    with pytest.raises(httpx.TransportError):
        httpx.post(f"{url}/chat/completions", json={"model": "m", "messages": []}, timeout=1)


# -- the embeddings route and the FakeEmbedder (feature 004) -------------------------------------------
def test_the_fake_server_answers_embeddings_from_its_table_or_a_hash(openai_server):
    import httpx

    openai_server.embed_dimensions = 4
    openai_server.embed_vectors["abre caminho"] = [1.0, 0.0]
    body = {"model": "m", "input": ["abre caminho", "outro"]}
    data = httpx.post(openai_server.base_url + "/embeddings", json=body).json()["data"]
    assert data[0]["embedding"] == [1.0, 0.0, 0.0, 0.0]
    assert len(data[1]["embedding"]) == 4 and data[1]["embedding"] != data[0]["embedding"]
    again = httpx.post(openai_server.base_url + "/embeddings", json=body).json()["data"]
    assert again[1]["embedding"] == data[1]["embedding"]  # deterministic


def test_the_fake_server_can_fail_embeddings(openai_server):
    import httpx

    openai_server.fail_status = 500
    assert httpx.post(openai_server.base_url + "/embeddings", json={"input": "x"}).status_code == 500


def test_the_fake_embedder_uses_its_table_records_calls_and_can_fail(embedder):
    fake = embedder({"a": [1.0]})
    assert fake.embed("a")[:2] == [1.0, 0.0] and len(fake.embed("b")) == 1024
    assert fake.calls == ["a", "b"]
    from pedido.embeddings import EmbeddingFailed

    with pytest.raises(EmbeddingFailed):
        embedder(fail=True).embed("x")
