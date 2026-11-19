"""Guardrails for the model (Constitution VIII): the model only reads orders, and stays inside limits.

Everything here is plain deterministic Python. Activations are logged by TYPE only: never the text
of the message, the phone number or any key.
"""
import logging
import math
import threading
import time
from collections import defaultdict, deque
from contextlib import contextmanager
from datetime import date, datetime, timezone
from zoneinfo import ZoneInfo

from pedido import config

log = logging.getLogger("pedido.guardrails")


def registrar(tipo: str) -> None:
    log.warning("guardrail=%s", tipo)


def _quantidade_valida(valor) -> bool:
    return (isinstance(valor, (int, float)) and not isinstance(valor, bool)
            and math.isfinite(valor) and valor > 0)


def _texto_valido(texto) -> bool:
    return isinstance(texto, str) and texto.strip() != "" and len(texto) <= config.max_texto_linha()


def validar_linhas(linhas: list) -> list:
    """Drop, silently, the lines with an invalid text or quantity, then keep at most MAX_LINHAS."""
    validas = [l for l in linhas if _texto_valido(l.texto) and _quantidade_valida(l.quantidade)]
    if len(validas) != len(linhas):
        registrar("linhas_invalidas")
    maximo = config.max_linhas()
    if len(validas) > maximo:
        registrar("linhas_demais")
        validas = validas[:maximo]
    return validas


def checar_quantidade(itens: list[tuple]) -> bool:
    """False when ONE product is above MAX_QTD_PRODUTO dozens (`itens` are already summed by product)."""
    limite = config.max_qtd_produto()
    return all(quantidade <= limite for _produto, quantidade in itens)


def checar_tamanho(texto: str) -> bool:
    return len(texto) <= config.max_mensagem()


class RateLimiter:
    """At most LIMITE_MSG_POR_MINUTO accepted messages per phone in a sliding window (kept in memory)."""

    def __init__(self, janela: float = 60.0, clock=time.monotonic, limite=None):
        """`limite`: a number or a callable returning it (read at every call); default LIMITE_MSG_POR_MINUTO."""
        self.janela, self.clock = janela, clock
        self._limite = limite if limite is not None else config.limite_msg_por_minuto
        self._aceitas: dict[str, deque] = defaultdict(deque)
        self._lock = threading.Lock()

    def permitir(self, telefone: str) -> bool:
        agora = self.clock()
        with self._lock:
            aceitas = self._aceitas[telefone]
            while aceitas and agora - aceitas[0] >= self.janela:
                aceitas.popleft()
            maximo = self._limite() if callable(self._limite) else self._limite
            if len(aceitas) >= maximo:
                return False  # a refused message is not counted: the block ends when the window slides
            aceitas.append(agora)
            return True


FUSO = ZoneInfo("America/Sao_Paulo")


def dia_atual(agora=None) -> date:
    """Today's date in the business timezone (the day the daily message limit counts)."""
    instante = (agora or (lambda: datetime.now(timezone.utc)))()
    return instante.astimezone(FUSO).date()


class Ocupado(Exception):
    """No slot for a language model call became free in time."""


class LimiteConcorrencia:
    """At most `maximo` language model calls at once; a caller waits up to `espera` seconds for a slot."""

    def __init__(self, maximo: int | None = None, espera: float | None = None):
        self._vagas = threading.BoundedSemaphore(maximo or config.max_llm_concorrentes())
        self._espera = espera

    @contextmanager
    def vaga(self):
        espera = self._espera if self._espera is not None else config.espera_llm_segundos()
        if not self._vagas.acquire(timeout=espera):
            raise Ocupado()
        try:
            yield
        finally:
            self._vagas.release()
