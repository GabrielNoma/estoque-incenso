"""The conversation engine (channel-agnostic): phone number and text in, reply text and optional file out.

It knows nothing about HTTP or WhatsApp. The reply to an order is only the list and "ok ou não?"
(Constitution III); everything that reads the customer's answer is deterministic (Constitution V).
"""
import logging
from dataclasses import dataclass

from pedido import config, guardrails, messages
from pedido.chains import build_export_chain, build_order_chain
from pedido.export import ProdutoAusente
from pedido.extract import ExtractionFailed
from pedido.llm import LLMNotConfigured
from pedido.lista import renderizar
from pedido.match import Matcher
from pedido.modelos import ModeloEstatico, ModeloIndisponivel
from pedido.normalize import normalize

log = logging.getLogger("pedido.conversa")

CONFIRMACOES = {"ok", "okay", "sim", "s", "confirmo", "confirmado", "isso", "certo", "blz", "pode", "beleza"}
RECUSAS = {"nao", "n", "cancelar", "cancela", "errado", "negativo"}


def interpretar(texto: str) -> str:
    """The whole message is ok, não, or (anything else) a new order."""
    limpo = normalize(texto, {})
    if limpo in CONFIRMACOES:
        return "ok"
    if limpo in RECUSAS:
        return "nao"
    return "pedido"


class ExportFailed(Exception):
    """The Excel could not be generated."""


class ModeloProdutoAusente(Exception):
    """A product of the pending order is not (or no longer the same) in the active model."""


class _Pipeline:
    """What depends on the active model: the matcher and the chains of one model version."""

    def __init__(self, modelo, chat_model, abbreviations, memoria):
        self.modelo = modelo
        self.matcher = Matcher(modelo.catalog, abbreviations=abbreviations,
                               apelidos=memoria.buscar if memoria is not None else None)
        self.chain = build_order_chain(self.matcher, chat_model)
        self.export_chain = build_export_chain(modelo.catalog, modelo.conteudo)
        self.nomes = {p.id: p.nome for p in modelo.catalog}


@dataclass
class Resposta:
    texto: str
    arquivo_nome: str | None = None
    arquivo_bytes: bytes | None = None
    pedido_id: int | None = None


def _linhas(resultado) -> list[dict]:
    return [{"texto": l.texto, "quantidade": l.quantidade, "produto_id": l.produto.id}
            for l in resultado.linhas]


class Conversa:
    def __init__(self, store, modelo, chat_model, abbreviations: dict[str, str] | None = None,
                 memoria=None, limitador=None, agora=None, concorrencia=None):
        """`modelo`: a ModeloService (the active model of the database) or a plain list of products."""
        self.limitador = limitador if limitador is not None else guardrails.RateLimiter()
        self.concorrencia = concorrencia if concorrencia is not None else guardrails.LimiteConcorrencia()
        self._agora = agora  # injectable clock (tests); default: the real time
        self.store = store
        self.modelos = modelo if hasattr(modelo, "atual") else ModeloEstatico(modelo)
        self.chat_model = chat_model
        self.abbreviations = abbreviations
        self.memoria = memoria
        self._pipeline_atual: _Pipeline | None = None

    def _pipeline(self) -> _Pipeline:
        """The matcher and chains of the ACTIVE model; rebuilt only when its version changes."""
        modelo = self.modelos.atual()  # raises ModeloIndisponivel
        atual = self._pipeline_atual
        if atual is None or atual.modelo.versao != modelo.versao:
            atual = self._pipeline_atual = _Pipeline(modelo, self.chat_model, self.abbreviations, self.memoria)
        return atual

    def _penalizar(self, pedido: dict) -> None:
        if self.memoria is None:
            return
        try:
            pipeline = self._pipeline()
        except ModeloIndisponivel:
            return  # no usable model: nothing to weigh, and the answer must not change
        self.memoria.agendar(self.memoria.penalizar, self._pares(pipeline, pedido["linhas"]))

    def _pares(self, pipeline: _Pipeline, linhas: list[dict]) -> list[tuple[str, int]]:
        """(normalized wording, product id) of each stored line; exact wordings are never remembered."""
        pares = []
        for linha in linhas:
            texto = normalize(linha["texto"], self.abbreviations)
            if len(texto) < 3 or pipeline.matcher.exata(linha["texto"]) is not None:
                continue
            pares.append((texto, linha["produto_id"]))
        return list(dict.fromkeys(pares))

    def responder(self, telefone: str, texto: str) -> Resposta:
        """Never raises: every failure becomes one short neutral sentence and the pending order stays."""
        try:
            return self._responder(telefone, texto)
        except (ExtractionFailed, LLMNotConfigured):
            return Resposta(messages.ERRO_LEITURA)
        except ExportFailed:
            return Resposta(messages.ERRO_PLANILHA)
        except ModeloIndisponivel:
            return Resposta(messages.MODELO_INVALIDO)
        except ModeloProdutoAusente:
            return Resposta(messages.MODELO_PRODUTO_AUSENTE)
        except Exception as error:  # database or anything unexpected; log the type only (no secrets)
            log.warning("falha ao responder: %s", type(error).__name__)
            return Resposta(messages.ERRO_BANCO)

    def _responder(self, telefone: str, texto: str) -> Resposta:
        if not self.limitador.permitir(telefone):
            guardrails.registrar("taxa")
            return Resposta(messages.MUITAS_MENSAGENS)
        dia = guardrails.dia_atual(self._agora)
        if self.store.registrar_mensagem(telefone, dia, config.limite_diario_conversa()) is None:
            guardrails.registrar("limite_diario")  # the model is never called; the pending order stays
            return Resposta(messages.LIMITE_DIARIO)
        acao = interpretar(texto)
        if acao == "pedido":
            return self._pedido(telefone, texto)
        pendente = self.store.get_pending(telefone)
        if pendente is None:
            return Resposta(messages.ENVIE_PEDIDO)
        if acao == "ok":
            return self._confirmar(pendente, texto)
        self.store.set_estado(pendente["id"], "recusado", texto)
        self._penalizar(pendente)
        return Resposta(messages.CANCELADO, pedido_id=pendente["id"])

    def _pedido(self, telefone: str, texto: str) -> Resposta:
        if not texto.strip():
            return Resposta(messages.SEM_ITENS)
        if not guardrails.checar_tamanho(texto):
            guardrails.registrar("mensagem_longa")
            return Resposta(messages.MENSAGEM_LONGA)
        pipeline = self._pipeline()  # the model must be usable BEFORE the language model is called
        if self.memoria is not None:
            self.memoria.nova_mensagem()
        try:
            with self.concorrencia.vaga():
                resultado = pipeline.chain.invoke(texto)
        except guardrails.Ocupado:
            guardrails.registrar("ocupado")
            return Resposta(messages.OCUPADO)
        if not resultado.itens:
            return Resposta(messages.SEM_ITENS)
        if not guardrails.checar_quantidade(resultado.itens):
            guardrails.registrar("quantidade_alta")
            return Resposta(messages.QUANTIDADE_ALTA)  # nothing stored; the pending order stays
        lista = renderizar(resultado.itens)
        stored = [{"produto_id": p.id, "nome": p.nome, "quantidade": q} for p, q in resultado.itens]
        anterior = self.store.get_pending(telefone) if self.memoria is not None else None
        pedido_id = self.store.create_pedido(telefone, texto, stored, lista, linhas=_linhas(resultado))
        if anterior is not None:
            self._penalizar(anterior)  # the replaced order gets a negative signal
        return Resposta(lista, pedido_id=pedido_id)

    def _confirmar(self, pendente: dict, texto: str) -> Resposta:
        pipeline = self._pipeline()
        for item in pendente["itens"]:  # every product must still be the same product in the active model
            nome = pipeline.nomes.get(item["produto_id"])
            if nome is None or (item.get("nome") is not None and item["nome"] != nome):
                raise ModeloProdutoAusente(str(item["produto_id"]))
        finals = [(item["produto_id"], item["quantidade"]) for item in pendente["itens"]]
        try:
            arquivo = pipeline.export_chain.invoke(finals)  # generated first: a failure leaves the order waiting
        except ProdutoAusente as error:
            raise ModeloProdutoAusente(str(error)) from error
        except Exception as error:
            raise ExportFailed(type(error).__name__) from error
        versao = pipeline.modelo.versao or None
        self.store.set_estado(pendente["id"], "confirmado", texto, modelo_versao=versao)
        if self.memoria is not None:
            self.memoria.agendar(self.memoria.aprender, self._pares(pipeline, pendente["linhas"]), pipeline.nomes)
        return Resposta(messages.CONFIRMADO, f"pedido-{pendente['id']}.xlsx", arquivo, pendente["id"])
