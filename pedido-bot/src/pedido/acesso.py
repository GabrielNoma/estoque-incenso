"""API keys, scopes and the per-key rate limit (Constitution IX; research D1, D2).

Keys come ONLY from the environment (`API_KEYS`), are compared in constant time against every key, and are
never stored or logged: a refusal logs the TYPE and, when known, the key's NAME.
"""
import hmac
import logging
import time
from dataclasses import dataclass, field

from fastapi import Request

from pedido import config, messages
from pedido.db import StartupError
from pedido.guardrails import RateLimiter

log = logging.getLogger("pedido.acesso")

ESCOPOS = frozenset({"conversa", "modelo"})
TAMANHO_MINIMO = 32

# Every route of the API and the scope it needs (None = public). A test walks the app against this table.
REGRAS: dict[tuple[str, str], str | None] = {
    ("GET", "/saude"): None,
    ("POST", "/api/mensagem"): "conversa",
    ("GET", "/api/pedidos/{pedido_id}/planilha"): "conversa",
    ("GET", "/api/modelo"): "modelo",
    ("POST", "/api/modelo"): "modelo",
    ("GET", "/api/modelo/info"): "modelo",
}


class ErroApi(Exception):
    """An API error: status, code and the Portuguese message (defaults to the one of `messages.ERROS`)."""

    def __init__(self, status: int, code: str, mensagem: str | None = None):
        super().__init__(code)
        self.status, self.code, self.mensagem = status, code, mensagem


@dataclass(frozen=True)
class Chave:
    nome: str
    escopos: frozenset
    segredo: str = field(repr=False)  # never shown, even by accident


def carregar_chaves(texto: str | None) -> list[Chave]:
    """Parse `name:scope+scope:key,...`. A bad entry stops the start with a message that never shows a key."""
    if not texto or not texto.strip():
        return []
    chaves: list[Chave] = []
    for n, entrada in enumerate(texto.split(","), start=1):
        if not entrada.strip():
            continue
        partes = entrada.strip().split(":", 2)
        if len(partes) != 3:
            raise StartupError(messages.ERRO_CHAVE_MALFORMADA.format(n=n))
        nome, escopos_texto, segredo = (p.strip() for p in partes)
        escopos = [e.strip() for e in escopos_texto.split("+") if e.strip()]
        if not nome or not escopos or len(segredo) < TAMANHO_MINIMO:
            raise StartupError(messages.ERRO_CHAVE_MALFORMADA.format(n=n))
        desconhecido = next((e for e in escopos if e not in ESCOPOS), None)
        if desconhecido:
            raise StartupError(messages.ERRO_ESCOPO_DESCONHECIDO.format(n=n, escopo=desconhecido))
        chaves.append(Chave(nome, frozenset(escopos), segredo))
    nomes = [c.nome for c in chaves]
    repetido = next((n for n in nomes if nomes.count(n) > 1), None)
    if repetido:
        raise StartupError(messages.ERRO_CHAVE_DUPLICADA.format(nome=repetido))
    return chaves


def registrar(tipo: str, nome: str | None = None) -> None:
    if nome:
        log.warning("acesso=%s chave=%s", tipo, nome)
    else:
        log.warning("acesso=%s", tipo)


class Acesso:
    def __init__(self, chaves: list[Chave], clock=time.monotonic):
        self.chaves = chaves
        self._limitador = RateLimiter(clock=clock, limite=config.limite_req_por_chave)

    @property
    def ativo(self) -> bool:
        return bool(self.chaves)

    @staticmethod
    def _token(headers) -> str | None:
        auth = headers.get("authorization", "")
        if auth[:7].lower() == "bearer ":  # Authorization wins over X-API-Key
            return auth[7:].strip() or None
        return (headers.get("x-api-key") or "").strip() or None

    def autenticar(self, headers, escopo: str) -> Chave | None:
        """The key of the request when it is valid, in scope and under its rate limit; otherwise `ErroApi`.
        With no keys configured (local use) it lets everything through and returns None."""
        if not self.ativo:
            return None
        token = self._token(headers)
        if token is None:
            registrar("chave_ausente")
            raise ErroApi(401, "chave_ausente")
        achada = None
        for chave in self.chaves:  # always against EVERY key: no early exit, constant time per key
            if hmac.compare_digest(token.encode("utf-8"), chave.segredo.encode("utf-8")):
                achada = chave
        if achada is None:
            registrar("chave_invalida")
            raise ErroApi(401, "chave_invalida")
        if escopo not in achada.escopos:
            registrar("sem_permissao", achada.nome)
            raise ErroApi(403, "sem_permissao")
        if not self._limitador.permitir(achada.nome):
            registrar("limite_chave", achada.nome)
            raise ErroApi(429, "muitas_requisicoes")
        return achada


def exigir(escopo: str):
    """A route dependency that requires a key with `escopo` (the attribute lets a test read the rule)."""

    def dependencia(request: Request) -> None:
        request.app.state.acesso.autenticar(request.headers, escopo)

    dependencia.escopo = escopo
    return dependencia
