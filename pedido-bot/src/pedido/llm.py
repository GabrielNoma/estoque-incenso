"""Language-model provider chosen by configuration (research D3, Constitution V).

`build_chat_model(env)` never raises for a missing key or address: the application must start
without them. The error (`LLMNotConfigured`) appears on first use, inside the extraction, where it
becomes the 001 behavior: a Portuguese message, the text kept and an empty table to fill by hand.
Keys are read from the environment only and never appear in representations or messages.
"""
import os

from pedido import config, messages

PROVIDERS = ("anthropic", "openai_compatible")


class LLMNotConfigured(Exception):
    """A needed setting is missing; the message names the variables (never their values)."""


class _AnthropicChat:
    def __init__(self, env):
        self._env = env

    def with_structured_output(self, schema, **kwargs):
        key = self._env.get("ANTHROPIC_API_KEY")
        if not key:
            raise LLMNotConfigured("ANTHROPIC_API_KEY")
        from langchain_anthropic import ChatAnthropic

        model = self._env.get("LLM_MODEL") or config.MODEL_NAME
        # Reading an order is an easy task: low effort, and no thinking at all on Haiku 5 (the other current
        # models refuse thinking "disabled"). The API refuses sampling parameters, so there is no temperature.
        light = {"thinking": {"type": "disabled"}} if model.startswith("claude-haiku-5") else {}
        chat = ChatAnthropic(model=model, api_key=key, max_retries=2, timeout=config.llm_timeout_seconds(),
                             max_tokens=config.llm_max_tokens(),
                             output_config={"effort": "low"}, **light)
        # native json_schema output: forced tool calling (the library default) is not supported
        # by claude-sonnet-5-5; LLM_STRUCTURED_METHOD=function_calling restores it if needed
        method = self._env.get("LLM_STRUCTURED_METHOD") or "json_schema"
        if method not in ("json_schema", "function_calling"):
            method = "json_schema"  # json_mode only exists for the OpenAI-compatible adapter
        return chat.with_structured_output(schema, method=method, **kwargs)

    def __repr__(self) -> str:
        return "AnthropicChat()"


class _OpenAICompatibleChat:
    def __init__(self, env):
        self._env = env

    def with_structured_output(self, schema, **kwargs):
        settings = {"LLM_BASE_URL": self._env.get("LLM_BASE_URL"),
                    "LLM_MODEL": self._env.get("LLM_MODEL"),
                    "LLM_API_KEY": self._env.get("LLM_API_KEY")}
        missing = [name for name, value in settings.items() if not value]
        if missing:
            raise LLMNotConfigured(", ".join(missing))
        from langchain_openai import ChatOpenAI

        chat = ChatOpenAI(base_url=settings["LLM_BASE_URL"], api_key=settings["LLM_API_KEY"],
                          model=settings["LLM_MODEL"], temperature=0, max_retries=0,
                          timeout=config.llm_timeout_seconds(), max_tokens=config.llm_max_tokens())
        method = self._env.get("LLM_STRUCTURED_METHOD") or "json_schema"
        return chat.with_structured_output(schema, method=method, **kwargs)

    def __repr__(self) -> str:
        return "OpenAICompatibleChat()"


def build_chat_model(env=None):
    env = dict(os.environ if env is None else env)
    provider = (env.get("LLM_PROVIDER") or "anthropic").strip()
    if provider == "anthropic":
        return _AnthropicChat(env)
    if provider == "openai_compatible":
        return _OpenAICompatibleChat(env)
    raise ValueError(messages.ERRO_LLM_PROVIDER_INVALIDO)
