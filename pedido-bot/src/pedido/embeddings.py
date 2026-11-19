"""The embedding service (Constitution V): used ONLY to look up and to store learned nicknames.

OpenAI-compatible (a local Ollama works). The key comes from the environment and never appears in a
representation or a message. Any problem becomes `EmbeddingFailed`; the callers treat it as "no memory".
"""
import os

from pedido import config


class EmbeddingFailed(Exception):
    """The service did not answer in time, answered an error, or returned a vector of another size."""


class Embedder:
    def __init__(self, base_url: str, model: str, api_key: str, dimensions: int, timeout: float,
                 enviar_dimensoes: bool = False):
        from langchain_openai import OpenAIEmbeddings

        self.model, self.dimensions = model, dimensions
        # Ollama needs the raw text (no token-length splitting); one try only: the wait must stay short
        extra = {"dimensions": dimensions} if enviar_dimensoes else {}  # hosted services can size the vector
        self._client = OpenAIEmbeddings(base_url=base_url, api_key=api_key or "sem-chave", model=model,
                                        check_embedding_ctx_length=False, timeout=timeout, max_retries=0, **extra)

    def embed(self, text: str) -> list[float]:
        try:
            vector = self._client.embed_query(text)
        except Exception as error:  # timeout, connection, HTTP status, malformed answer
            raise EmbeddingFailed(type(error).__name__) from error
        if len(vector) != self.dimensions:
            raise EmbeddingFailed(f"vetor de tamanho {len(vector)}, esperado {self.dimensions}")
        return list(vector)

    def __repr__(self) -> str:
        return f"Embedder(model={self.model!r})"


def build_embedder(env=None) -> Embedder | None:
    """None when the memory is not configured (the bot then behaves exactly as without it)."""
    env = os.environ if env is None else env
    base_url, model = env.get("EMBED_BASE_URL"), env.get("EMBED_MODEL")
    if not base_url or not model:
        return None
    def number(name, default, kind=int):
        try:
            value = kind(env.get(name, ""))
        except ValueError:
            return default
        return value if value > 0 else default
    enviar = str(env.get("EMBED_SEND_DIMENSIONS", "")).strip().lower() in ("1", "true", "sim", "yes")
    return Embedder(base_url, model, env.get("EMBED_API_KEY", ""), number("EMBED_DIMENSIONS", 1024),
                    number("EMBED_TIMEOUT_SECONDS", 5), enviar)
