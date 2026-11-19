"""FastAPI app: the simple chat page plus the JSON API of contracts/http-api.md.

Every error body is {"erro": code, "mensagem": <pt-BR text from pedido.messages>}.
"""
import logging
import os
from pathlib import Path
from urllib.parse import unquote

from fastapi import Depends, FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import HTMLResponse, JSONResponse, Response
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel

from pedido import config, guardrails, messages
from pedido.acesso import Acesso, ErroApi as ApiError, carregar_chaves, exigir
from pedido.catalog import ModeloInvalido
from pedido.chains import build_export_chain
from pedido.conversa import Conversa
from pedido.db import StartupError, check_database
from pedido.embeddings import build_embedder
from pedido.llm import build_chat_model
from pedido.memoria import Memoria
from pedido.modelos import ModeloIndisponivel, ModeloService
from pedido.normalize import load_abbreviations
from pedido.store import Store

WEB_DIR = Path(__file__).resolve().parent
XLSX_TYPE = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"


class Mensagem(BaseModel):
    telefone: str
    texto: str


FROM_ENV = object()  # create_app default: build the embedder from the environment (None = memory off)


log = logging.getLogger("pedido.web")


async def limitar_corpo(request: Request) -> None:
    """A message request body above MAX_CORPO_MENSAGEM_KB is refused (413) before anything is parsed."""
    limite = config.max_corpo_mensagem_kb() * 1024
    declarado = request.headers.get("content-length")
    if declarado and declarado.isdigit() and int(declarado) > limite:
        guardrails.registrar("corpo_grande")
        raise ApiError(413, "corpo_grande")
    if len(await request.body()) > limite:
        guardrails.registrar("corpo_grande")
        raise ApiError(413, "corpo_grande")


def create_app(database_url=None, chat_model=None, template_path=None, embedder=FROM_ENV,
               executor=None, api_keys=FROM_ENV) -> FastAPI:
    producao = config.ambiente() == "producao"
    texto_chaves = os.environ.get("API_KEYS") if api_keys is FROM_ENV else api_keys
    chaves = carregar_chaves(texto_chaves)  # raises StartupError (pt-BR) on a bad entry
    if producao and not chaves:
        raise StartupError(messages.ERRO_CHAVES_AUSENTES)
    if not chaves:
        log.warning("API_KEYS não configurada: controle de acesso desligado (uso local). "
                    "Configure API_KEYS antes de expor o serviço.")
    # in production there is no page and no API documentation
    app = FastAPI(title="Bot de pedidos",
                  **({"docs_url": None, "redoc_url": None, "openapi_url": None} if producao else {}))
    app.state.acesso = Acesso(chaves)
    url = database_url or config.database_url()
    check_database(url, config.embed_dimensions())  # raises StartupError (pt-BR) when unusable
    store = Store(url)
    modelos = ModeloService(store, load_abbreviations())
    modelos.iniciar()  # the seed model on a fresh database; the catalog and the nickname names follow it
    chat = chat_model if chat_model is not None else build_chat_model()
    embedder = build_embedder() if embedder is FROM_ENV else embedder
    memoria = Memoria(store, embedder, executor=executor) if embedder is not None else None
    conversa = Conversa(store, modelos, chat, abbreviations=load_abbreviations(), memoria=memoria)
    app.state.store, app.state.modelos, app.state.memoria = store, modelos, memoria

    if not producao:
        templates = Jinja2Templates(directory=str(WEB_DIR / "templates"))
        app.mount("/static", StaticFiles(directory=str(WEB_DIR / "static")), name="static")

    # -- errors, always in pt-BR ----------------------------------------------------------
    def error_body(code: str, mensagem: str | None = None) -> dict:
        return {"erro": code, "mensagem": mensagem or messages.ERROS[code]}

    @app.exception_handler(ApiError)
    async def api_error(_request: Request, exc: ApiError):
        return JSONResponse(error_body(exc.code, exc.mensagem), status_code=exc.status)

    @app.exception_handler(RequestValidationError)
    async def invalid_request(_request: Request, _exc: RequestValidationError):
        return JSONResponse(error_body("requisicao_invalida"), status_code=422)

    @app.exception_handler(Exception)
    async def unexpected_error(_request: Request, _exc: Exception):
        return JSONResponse(error_body("erro_interno"), status_code=500)

    # -- page and API -----------------------------------------------------------------------
    if not producao:
        @app.get("/", response_class=HTMLResponse)
        async def home(request: Request):
            return templates.TemplateResponse(request, "index.html", {"m": messages})

    @app.post("/api/mensagem", dependencies=[Depends(exigir("conversa")), Depends(limitar_corpo)])
    def mensagem(body: Mensagem):
        resposta = conversa.responder(body.telefone.strip(), body.texto)
        arquivo = None
        if resposta.arquivo_bytes is not None:
            arquivo = {"nome": resposta.arquivo_nome, "url": f"/api/pedidos/{resposta.pedido_id}/planilha"}
        return {"resposta": resposta.texto, "arquivo": arquivo}

    @app.get("/saude")
    def saude():
        """Public, no key, no detail: the platform asks this to know whether the service is alive."""
        try:
            store.ping()
        except Exception as error:
            log.warning("saude=indisponivel tipo=%s", type(error).__name__)
            return JSONResponse({"status": "indisponivel"}, status_code=503)
        return {"status": "ok"}

    @app.get("/api/pedidos/{pedido_id}/planilha", dependencies=[Depends(exigir("conversa"))])
    def planilha(pedido_id: int):
        pedido = store.get_pedido(pedido_id)
        if pedido is None:
            raise ApiError(404, "pedido_nao_encontrado")
        if pedido["estado"] != "confirmado":
            raise ApiError(409, "pedido_nao_confirmado")
        finals = [(item["produto_id"], item["quantidade"]) for item in pedido["itens"]]
        try:  # the Excel is regenerated from the model version the order was confirmed with
            modelo = modelos.por_versao(pedido["modelo_versao"]) if pedido["modelo_versao"] else modelos.atual()
            conteudo = build_export_chain(modelo.catalog, modelo.conteudo).invoke(finals)
        except ModeloIndisponivel:
            raise ApiError(503, "modelo_indisponivel")
        nome = f"pedido-{pedido_id}.xlsx"
        return Response(conteudo, media_type=XLSX_TYPE,
                        headers={"Content-Disposition": f'attachment; filename="{nome}"'})

    # -- the order-form model ---------------------------------------------------------------------
    @app.get("/api/modelo", dependencies=[Depends(exigir("modelo"))])
    def baixar_modelo():
        try:
            ativo = modelos.atual()
        except ModeloIndisponivel:
            raise ApiError(503, "modelo_indisponivel")
        return Response(ativo.conteudo, media_type=XLSX_TYPE,
                        headers={"Content-Disposition": 'attachment; filename="modelo-pedido.xlsx"'})

    @app.get("/api/modelo/info", dependencies=[Depends(exigir("modelo"))])
    def info_modelo():
        try:
            return modelos.info()
        except ModeloIndisponivel:
            raise ApiError(503, "modelo_indisponivel")

    @app.post("/api/modelo", dependencies=[Depends(exigir("modelo"))])
    async def importar_modelo(request: Request):
        limite = config.max_modelo_mb()
        mensagem_grande = messages.MODELO_GRANDE.format(limite=limite)
        if int(request.headers.get("content-length") or 0) > limite * 1024 * 1024:
            raise ApiError(413, "modelo_grande", mensagem_grande)
        conteudo = await request.body()
        if len(conteudo) > limite * 1024 * 1024:
            raise ApiError(413, "modelo_grande", mensagem_grande)
        nome = unquote(request.headers.get("x-nome-arquivo") or "") or None
        try:
            return modelos.importar(conteudo, nome)
        except ModeloInvalido as erro:
            raise ApiError(422, "modelo_invalido", erro.mensagem)

    return app
