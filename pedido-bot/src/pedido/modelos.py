"""Which order-form model is active (Constitution IV and VI; research D1, D4).

The models live in Postgres, with versions; the repository file is only the seed. The catalog of the
active model is rebuilt only when its version changes, so a model imported by anyone is used by the next
message with no restart.
"""
import logging
import threading
from dataclasses import dataclass

from pedido import config
from pedido.catalog import load_catalog, validar_modelo

log = logging.getLogger("pedido.modelos")

NOME_SEMENTE = "PLANILHA_2024.xlsx"


class ModeloIndisponivel(Exception):
    """The active model cannot be read or has no products."""


@dataclass
class ModeloAtivo:
    versao: int
    arquivo: str
    catalog: list
    conteudo: bytes
    ativado_em: str | None = None

    @property
    def produtos(self) -> int:
        return len(self.catalog)


def comparar(antigo: list, novo: list) -> dict:
    """What a new model adds, removes and renames, by position (id) and name."""
    a = {p.id: p.nome for p in antigo}
    n = {p.id: p.nome for p in novo}
    ordem = {p.id: (p.bloco, p.linha) for p in antigo + novo}
    por_posicao = lambda ids: sorted(ids, key=lambda i: ordem[i])  # noqa: E731
    return {
        "adicionados": [n[i] for i in por_posicao(n.keys() - a.keys())],
        "removidos": [a[i] for i in por_posicao(a.keys() - n.keys())],
        "renomeados": [{"de": a[i], "para": n[i]} for i in por_posicao(a.keys() & n.keys()) if a[i] != n[i]],
    }


class ModeloService:
    def __init__(self, store, abbreviations: dict[str, str] | None = None):
        self.store = store
        self.abbreviations = abbreviations
        self._cache: ModeloAtivo | None = None
        self._lock = threading.RLock()

    # -- startup -------------------------------------------------------------------------------
    def garantir_semente(self) -> None:
        """Install the repository file as version 1 when the database holds no model at all."""
        if self.store.listar_modelos():
            return
        conteudo = config.TEMPLATE_PATH.read_bytes()
        catalog = validar_modelo(conteudo, self.abbreviations)
        self.store.salvar_modelo(NOME_SEMENTE, conteudo, len(catalog))

    def iniciar(self) -> None:
        """Seed, keep the `catalog` table and the nickname names in step with the active model."""
        self.garantir_semente()
        ativo = self.atual()
        self.store.save_catalog(ativo.catalog)
        self.store.sincronizar_apelidos(ativo.catalog)

    # -- reading ---------------------------------------------------------------------------------
    def _montar(self, row: dict) -> ModeloAtivo:
        try:
            catalog = load_catalog(row["conteudo"], self.abbreviations)
        except Exception as error:
            raise ModeloIndisponivel(type(error).__name__) from error
        if not catalog:
            raise ModeloIndisponivel("sem produtos")
        return ModeloAtivo(row["versao"], row["arquivo"], catalog, row["conteudo"], row["criado_em"])

    def atual(self) -> ModeloAtivo:
        versao = self.store.versao_ativa()
        if versao is None:
            raise ModeloIndisponivel("nenhum modelo")
        with self._lock:
            if self._cache is not None and self._cache.versao == versao:
                return self._cache
            row = self.store.get_modelo(versao)
            self._cache = self._montar(row)
            return self._cache

    def por_versao(self, versao: int) -> ModeloAtivo:
        row = self.store.get_modelo(versao)
        if row is None:
            raise ModeloIndisponivel(f"versão {versao}")
        return self._montar(row)

    def info(self) -> dict:
        ativo = self.atual()
        return {"versao": ativo.versao, "arquivo": ativo.arquivo, "produtos": ativo.produtos,
                "ativado_em": ativo.ativado_em}

    # -- changing --------------------------------------------------------------------------------
    def importar(self, conteudo: bytes, arquivo: str | None = None) -> dict:
        """Validate and activate a new model. `ModeloInvalido` leaves everything as it was."""
        novo = validar_modelo(conteudo, self.abbreviations)
        with self._lock:
            try:
                antigo = self.atual().catalog
            except ModeloIndisponivel:
                antigo = []
            versao = self.store.salvar_modelo((arquivo or "modelo.xlsx")[:200], conteudo, len(novo))
            self.store.save_catalog(novo)
            desativados = self.store.sincronizar_apelidos(novo)
            self._cache = None
        log.info("modelo ativado: versão %s com %s produtos", versao, len(novo))
        return {"versao": versao, "arquivo": (arquivo or "modelo.xlsx")[:200], "produtos": len(novo),
                **comparar(antigo, novo), "apelidos_desativados": desativados}


class ModeloEstatico:
    """A fixed list of products (no database): used by tests and simple setups. Version 0, seed template."""

    def __init__(self, catalog: list):
        self._ativo = ModeloAtivo(0, "", catalog, None, None)

    def atual(self) -> ModeloAtivo:
        return self._ativo
