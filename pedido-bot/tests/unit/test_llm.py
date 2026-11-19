"""LLM provider adapters (research D3, tasks T024). The OpenAI-compatible side talks to a fake server."""
import pytest

from pedido import messages
from pedido.extract import ExtracaoPedido
from pedido.llm import LLMNotConfigured, build_chat_model

KEY = "chave-secreta-xyz"
ANSWER = {"linhas": [{"texto": "ogum", "quantidade": 2, "unidade": "dz"}]}


def compat_env(server, **extra):
    env = {"LLM_PROVIDER": "openai_compatible", "LLM_BASE_URL": server.base_url,
           "LLM_MODEL": "modelo-x", "LLM_API_KEY": KEY}
    env.update(extra)
    return env


def test_anthropic_is_built_lazily_without_a_key():
    chat = build_chat_model({"LLM_PROVIDER": "anthropic"})  # nothing raised at build time
    with pytest.raises(LLMNotConfigured):
        chat.with_structured_output(ExtracaoPedido)  # first use needs ANTHROPIC_API_KEY


def test_anthropic_with_a_key_builds_the_claude_adapter_without_network():
    chat = build_chat_model({"LLM_PROVIDER": "anthropic", "ANTHROPIC_API_KEY": "sk-teste"})
    assert chat.with_structured_output(ExtracaoPedido) is not None


def test_anthropic_uses_native_json_schema_not_forced_tool_calling():
    # claude-sonnet-5-5 does not support structured output through forced tool calling (the library
    # warns about it), so the default must be the native json_schema output.
    chat = build_chat_model({"LLM_PROVIDER": "anthropic", "ANTHROPIC_API_KEY": "sk-teste"})
    bound = chat.with_structured_output(ExtracaoPedido).first.kwargs
    assert "output_config" in bound and "tools" not in bound


def test_anthropic_can_still_be_switched_to_function_calling_by_configuration():
    chat = build_chat_model({"LLM_PROVIDER": "anthropic", "ANTHROPIC_API_KEY": "sk-teste",
                             "LLM_STRUCTURED_METHOD": "function_calling"})
    bound = chat.with_structured_output(ExtracaoPedido).first.kwargs
    assert "tools" in bound


def test_anthropic_is_the_default_provider():
    with pytest.raises(LLMNotConfigured):
        build_chat_model({}).with_structured_output(ExtracaoPedido)


def test_openai_compatible_sends_the_request_and_parses_the_structured_answer(openai_server):
    openai_server.chat_answers.append(ANSWER)
    chat = build_chat_model(compat_env(openai_server))
    result = chat.with_structured_output(ExtracaoPedido).invoke("2 dz de ogum")
    assert isinstance(result, ExtracaoPedido) and result.linhas[0].texto == "ogum"
    (seen,) = openai_server.requests
    assert seen["path"] == "/v1/chat/completions"
    assert seen["authorization"] == f"Bearer {KEY}"
    assert seen["json"]["model"] == "modelo-x"
    assert seen["json"]["response_format"]["type"] == "json_schema"


def test_function_calling_can_be_selected_for_services_without_schema_support(openai_server):
    openai_server.chat_answers.append(ANSWER)
    chat = build_chat_model(compat_env(openai_server, LLM_STRUCTURED_METHOD="function_calling"))
    result = chat.with_structured_output(ExtracaoPedido).invoke("2 dz de ogum")
    assert result.linhas[0].quantidade == 2
    assert "tools" in openai_server.requests[0]["json"]


@pytest.mark.parametrize("missing", ["LLM_BASE_URL", "LLM_MODEL", "LLM_API_KEY"])
def test_openai_compatible_without_address_model_or_key_fails_on_first_use(openai_server, missing):
    env = compat_env(openai_server)
    del env[missing]
    chat = build_chat_model(env)  # building never raises: the app must start without a key
    with pytest.raises(LLMNotConfigured) as error:
        chat.with_structured_output(ExtracaoPedido)
    assert missing in str(error.value)


def test_an_invalid_provider_is_rejected():
    with pytest.raises(ValueError, match=messages.ERRO_LLM_PROVIDER_INVALIDO):
        build_chat_model({"LLM_PROVIDER": "gpt"})


def test_the_key_never_appears_in_representations_or_errors(openai_server):
    chat = build_chat_model(compat_env(openai_server))
    assert KEY not in repr(chat) and KEY not in str(chat)
    assert KEY not in repr(chat.with_structured_output(ExtracaoPedido))
    openai_server.fail_status = 500
    with pytest.raises(Exception) as error:
        chat.with_structured_output(ExtracaoPedido).invoke("x")
    assert KEY not in str(error.value)


def test_the_openai_compatible_adapter_uses_the_configured_timeout(monkeypatch, openai_server):
    from pedido import llm
    from pydantic import BaseModel

    class Esquema(BaseModel):
        x: int = 1

    seen = {}
    real = __import__("langchain_openai").ChatOpenAI

    def spy(**kwargs):
        seen.update(kwargs)
        return real(**kwargs)

    monkeypatch.setattr("langchain_openai.ChatOpenAI", spy)
    monkeypatch.setenv("LLM_TIMEOUT_SECONDS", "321")
    chat = llm.build_chat_model({"LLM_PROVIDER": "openai_compatible", "LLM_BASE_URL": openai_server.base_url,
                                 "LLM_MODEL": "m", "LLM_API_KEY": "k"})
    chat.with_structured_output(Esquema)
    assert seen["timeout"] == 321 and seen["max_retries"] == 0  # the retry belongs to the extraction (once)


# -- the Claude adapter: no sampling parameters (the API refuses them), light settings for extraction ------
def _spy_anthropic(monkeypatch):
    from pydantic import BaseModel

    class Esquema(BaseModel):
        x: int = 1

    seen = {}
    real = __import__("langchain_anthropic").ChatAnthropic

    def spy(**kwargs):
        seen.update(kwargs)
        return real(**kwargs)

    monkeypatch.setattr("langchain_anthropic.ChatAnthropic", spy)
    return seen, Esquema


def test_the_claude_adapter_sends_no_sampling_parameters_and_asks_for_low_effort(monkeypatch):
    from pedido import llm

    seen, Esquema = _spy_anthropic(monkeypatch)
    llm.build_chat_model({"LLM_PROVIDER": "anthropic", "ANTHROPIC_API_KEY": "k", "LLM_MODEL": "claude-sonnet-5-5"}) \
        .with_structured_output(Esquema)
    assert "temperature" not in seen and "top_p" not in seen and "top_k" not in seen
    assert seen["output_config"] == {"effort": "low"}
    assert "thinking" not in seen  # Sonnet 5.5 refuses thinking "disabled"


def test_haiku_runs_without_thinking_because_reading_an_order_is_not_a_hard_task(monkeypatch):
    from pedido import llm

    seen, Esquema = _spy_anthropic(monkeypatch)
    llm.build_chat_model({"LLM_PROVIDER": "anthropic", "ANTHROPIC_API_KEY": "k", "LLM_MODEL": "claude-haiku-5-5"}) \
        .with_structured_output(Esquema)
    assert seen["thinking"] == {"type": "disabled"} and seen["output_config"] == {"effort": "low"}


# -- feature 006: an explicit maximum output for every call to the language model ------------------------------
def test_the_default_maximum_output_is_4096_tokens(monkeypatch):
    from pedido import config

    monkeypatch.delenv("LLM_MAX_TOKENS", raising=False)
    assert config.llm_max_tokens() == 4096


def test_the_claude_adapter_passes_the_maximum_output(monkeypatch):
    from pedido import llm

    seen, Esquema = _spy_anthropic(monkeypatch)
    monkeypatch.setenv("LLM_MAX_TOKENS", "1234")
    llm.build_chat_model({"LLM_PROVIDER": "anthropic", "ANTHROPIC_API_KEY": "k"}).with_structured_output(Esquema)
    assert seen["max_tokens"] == 1234


def test_the_openai_compatible_adapter_sends_the_maximum_output_to_the_server(monkeypatch, openai_server):
    from pedido import llm
    from pydantic import BaseModel

    class Esquema(BaseModel):
        x: int = 1

    monkeypatch.setenv("LLM_MAX_TOKENS", "777")
    openai_server.chat_answers.append({"x": 1})
    chat = llm.build_chat_model({"LLM_PROVIDER": "openai_compatible", "LLM_BASE_URL": openai_server.base_url,
                                 "LLM_MODEL": "m", "LLM_API_KEY": "k"})
    chat.with_structured_output(Esquema).invoke("oi")
    corpo = openai_server.requests[-1]["json"]
    assert (corpo.get("max_tokens") or corpo.get("max_completion_tokens")) == 777
