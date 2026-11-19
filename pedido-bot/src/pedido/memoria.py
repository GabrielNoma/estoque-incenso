"""The silent nickname memory (Constitution IV and VI).

It looks up learned nicknames while matching and learns from the customers' answers, but it is only a
helper: every error is swallowed and logged by type, so the reply never changes, breaks or waits for
it. Writes run in a single background worker, after the reply was built.
"""
import logging
import threading
from concurrent.futures import ThreadPoolExecutor

from pedido import config
from pedido.embeddings import EmbeddingFailed

log = logging.getLogger("pedido.memoria")


class Memoria:
    def __init__(self, store, embedder=None, executor=None, similarity: float | None = None):
        self.store = store
        self.embedder = embedder
        self.similarity = similarity  # None: read EMBED_SIMILARITY on every lookup
        self._executor = executor if executor is not None else ThreadPoolExecutor(max_workers=1)
        self._state = threading.local()  # per message (each message is handled in one thread)

    def nova_mensagem(self) -> None:
        """A new message starts: an embedding failure only silences the embedder for ONE message."""
        self._state.embedding_falhou = False

    # -- reading ------------------------------------------------------------------------------
    def buscar(self, texto: str) -> int | None:
        """Product id of an applying nickname for this normalized wording, or None. Never raises."""
        try:
            produto_id = self.store.buscar_exato(texto)
            if produto_id is not None:
                return produto_id
            if self.embedder is None or getattr(self._state, "embedding_falhou", False):
                return None
            if not self.store.tem_apelidos(self.embedder.model):
                return None
            try:
                vector = self.embedder.embed(texto)
            except EmbeddingFailed as error:
                self._state.embedding_falhou = True
                log.warning("embedding indisponível: %s", error.__class__.__name__)
                return None
            limiar = self.similarity if self.similarity is not None else config.embed_similarity()
            return self.store.buscar_similar(vector, self.embedder.model, limiar)
        except Exception as error:
            log.warning("consulta da memória falhou: %s", type(error).__name__)
            return None

    # -- writing (always through `agendar`) -----------------------------------------------------
    def aprender(self, pares: list[tuple[str, int]], nomes: dict[int, str] | None = None) -> None:
        """One positive for each (normalized wording, product id); `nomes` maps ids to product names.
        Never raises."""
        asking = self.embedder is not None
        for texto, produto_id in pares:
            vector = None
            if asking:
                try:
                    vector = self.embedder.embed(texto)
                except EmbeddingFailed as error:
                    asking = False  # the rest of the batch is stored without a vector
                    log.warning("embedding indisponível: %s", error.__class__.__name__)
            try:
                self.store.upsert_positivo(texto, produto_id, vector,
                                           self.embedder.model if vector is not None else None,
                                           (nomes or {}).get(produto_id))
            except Exception as error:
                log.warning("gravação na memória falhou: %s", type(error).__name__)

    def penalizar(self, pares: list[tuple[str, int]]) -> None:
        """One negative for each existing (normalized wording, product id). Never raises."""
        for texto, produto_id in pares:
            try:
                self.store.penalizar(texto, produto_id)
            except Exception as error:
                log.warning("gravação na memória falhou: %s", type(error).__name__)

    def agendar(self, fn, *args) -> None:
        """Run `fn` off the reply path; its errors are swallowed."""
        def run():
            try:
                fn(*args)
            except Exception as error:
                log.warning("tarefa da memória falhou: %s", type(error).__name__)

        self._executor.submit(run)


def reindexar(store, embedder) -> tuple[int, int]:
    """Recompute the embedding of EVERY stored nickname with the current model (nothing is deleted).
    Returns (done, failed); a failing service only counts the failures and keeps the successes."""
    feitos = falhas = 0
    for apelido in store.list_apelidos():
        try:
            store.atualizar_embedding(apelido["id"], embedder.embed(apelido["texto_normalizado"]), embedder.model)
            feitos += 1
        except Exception as error:  # EmbeddingFailed, database error...
            falhas += 1
            log.warning("reindexar falhou: %s", type(error).__name__)
    return feitos, falhas
