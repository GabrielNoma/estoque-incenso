"""Postgres persistence: the catalog and the orders of each phone number (data-model.md).

One connection per operation, always through `Store._connect()`; each operation is one transaction
(commit on success, rollback on any error), so an order is never left half-saved. Timestamps leave this
module as ISO-8601 strings. An order only moves forward: aguardando -> confirmado | recusado, or
aguardando -> substituido when a new order of the same phone replaces it.
"""
from contextlib import contextmanager

from pgvector import Vector
from pgvector.psycopg import register_vector
from psycopg.rows import dict_row
from psycopg.types.json import Jsonb

from pedido.db import connect

ANSWERS = ("confirmado", "recusado")


class InvalidTransition(Exception):
    """The order is not waiting for an answer, or the target state is not an answer."""


def _iso(value):
    return None if value is None else value.isoformat(timespec="seconds")


def _pedido(row: dict) -> dict:
    row = dict(row)
    row["criado_em"] = _iso(row["criado_em"])
    row["respondido_em"] = _iso(row["respondido_em"])
    return row


class Store:
    def __init__(self, url: str):
        self.url = url

    @contextmanager
    def _connect(self):
        conn = connect(self.url)
        register_vector(conn)
        conn.row_factory = dict_row
        with conn:  # commit on success, rollback on error, always close
            yield conn

    def ping(self) -> None:
        """Raises when the database does not answer (used by the health check)."""
        with self._connect() as db:
            db.execute("select 1").fetchone()

    # -- catalog ---------------------------------------------------------------------------
    def save_catalog(self, products) -> None:
        with self._connect() as db, db.cursor() as cur:
            cur.executemany(
                "insert into pedido.catalog (id, nome, nome_normalizado, categoria, bloco, linha, "
                "celula_qtd) values (%s, %s, %s, %s, %s, %s, %s) on conflict (id) do update set "
                "nome = excluded.nome, nome_normalizado = excluded.nome_normalizado, "
                "categoria = excluded.categoria, bloco = excluded.bloco, linha = excluded.linha, "
                "celula_qtd = excluded.celula_qtd",
                [(p.id, p.nome, p.nome_normalizado, p.categoria, p.bloco, p.linha, p.celula_qtd)
                 for p in products])

    # -- orders ----------------------------------------------------------------------------
    def create_pedido(self, telefone: str, mensagem: str, itens: list[dict], lista: str,
                      linhas: list[dict] | None = None) -> int:
        """Save a new waiting order; the phone's previous waiting order becomes `substituido` in the
        SAME transaction, so there is never more than one waiting order per phone."""
        with self._connect() as db:
            db.execute("update pedido.pedidos set estado = 'substituido', respondido_em = now() "
                       "where telefone = %s and estado = 'aguardando'", (telefone,))
            return db.execute(
                "insert into pedido.pedidos (telefone, mensagem, itens, lista, linhas) "
                "values (%s, %s, %s, %s, %s) returning id",
                (telefone, mensagem, Jsonb(itens), lista, Jsonb(linhas or []))).fetchone()["id"]

    def get_pending(self, telefone: str) -> dict | None:
        with self._connect() as db:
            row = db.execute("select * from pedido.pedidos where telefone = %s and estado = 'aguardando' "
                             "order by id desc limit 1", (telefone,)).fetchone()
        return _pedido(row) if row else None

    def get_pedido(self, pedido_id: int) -> dict | None:
        with self._connect() as db:
            row = db.execute("select * from pedido.pedidos where id = %s", (pedido_id,)).fetchone()
        return _pedido(row) if row else None

    def set_estado(self, pedido_id: int, estado: str, resposta: str | None = None,
                   modelo_versao: int | None = None) -> None:
        """Close a waiting order with the customer's answer (`confirmado` or `recusado`)."""
        if estado not in ANSWERS:
            raise InvalidTransition(estado)
        with self._connect() as db:
            closed = db.execute(
                "update pedido.pedidos set estado = %s, resposta = %s, respondido_em = now(), "
                "modelo_versao = %s where id = %s and estado = 'aguardando' returning id",
                (estado, resposta, modelo_versao, pedido_id)).fetchone()
        if closed is None:
            raise InvalidTransition(f"order {pedido_id} is not waiting for an answer")

    def list_pedidos(self, telefone: str | None = None) -> list[dict]:
        with self._connect() as db:
            if telefone is None:
                rows = db.execute("select * from pedido.pedidos order by id desc").fetchall()
            else:
                rows = db.execute("select * from pedido.pedidos where telefone = %s order by id desc",
                                  (telefone,)).fetchall()
        return [_pedido(r) for r in rows]

    # -- the nickname memory (data-model.md) ------------------------------------------------
    APLICA = "status = 'ativo' and positivos >= 2 and positivos > negativos"

    def upsert_positivo(self, texto: str, produto_id: int, vetor: list[float] | None = None,
                        modelo: str | None = None, produto_nome: str | None = None) -> None:
        """One more confirmation of this wording for this product (keeps the latest embedding)."""
        embedding = None if vetor is None else Vector(vetor)
        with self._connect() as db:
            db.execute(
                "insert into pedido.apelidos (texto_normalizado, produto_id, embedding, modelo, positivos, "
                "produto_nome) values (%s, %s, %s, %s, 1, %s) "
                "on conflict (texto_normalizado, produto_id) do update set "
                "positivos = pedido.apelidos.positivos + 1, "
                "produto_nome = coalesce(pedido.apelidos.produto_nome, excluded.produto_nome), "
                "embedding = coalesce(excluded.embedding, pedido.apelidos.embedding), "
                "modelo = case when excluded.embedding is not null then excluded.modelo "
                "else pedido.apelidos.modelo end, atualizado_em = now()",
                (texto, produto_id, embedding, modelo if embedding is not None else None, produto_nome))

    def penalizar(self, texto: str, produto_id: int) -> bool:
        """One negative signal for an EXISTING wording; never creates or deletes a row."""
        with self._connect() as db:
            row = db.execute(
                "update pedido.apelidos set negativos = negativos + 1, atualizado_em = now() "
                "where texto_normalizado = %s and produto_id = %s returning id", (texto, produto_id)).fetchone()
        return row is not None

    def buscar_exato(self, texto: str) -> int | None:
        """The product of the learned nickname with exactly this normalized text (best balance first)."""
        with self._connect() as db:
            row = db.execute(
                f"select produto_id from pedido.apelidos where texto_normalizado = %s and {self.APLICA} "
                "order by positivos - negativos desc, produto_id limit 1", (texto,)).fetchone()
        return row["produto_id"] if row else None

    def buscar_similar(self, vetor: list[float], modelo: str, limiar: float) -> int | None:
        """The product of the closest applying nickname of THIS model with cosine similarity >= limiar."""
        query = Vector(vetor)
        with self._connect() as db:
            row = db.execute(
                f"select produto_id from pedido.apelidos where {self.APLICA} and modelo = %s "
                "and embedding is not null and 1 - (embedding <=> %s) >= %s "
                "order by embedding <=> %s, positivos - negativos desc, produto_id limit 1",
                (modelo, query, limiar, query)).fetchone()
        return row["produto_id"] if row else None

    def tem_apelidos(self, modelo: str) -> bool:
        """Could a similarity search of this model find anything? (saves a useless embedding call)"""
        with self._connect() as db:
            row = db.execute(f"select 1 from pedido.apelidos where {self.APLICA} and modelo = %s "
                             "and embedding is not null limit 1", (modelo,)).fetchone()
        return row is not None

    def set_status(self, apelido_id: int, status: str) -> bool:
        if status not in ("ativo", "desativado"):
            raise ValueError(status)
        with self._connect() as db:
            row = db.execute("update pedido.apelidos set status = %s, atualizado_em = now() "
                             "where id = %s returning id", (status, apelido_id)).fetchone()
        return row is not None

    def list_apelidos(self) -> list[dict]:
        with self._connect() as db:
            rows = db.execute(
                f"select id, texto_normalizado, produto_id, produto_nome, modelo, positivos, negativos, status, "
                f"({self.APLICA}) as aplica from pedido.apelidos order by id").fetchall()
        return [dict(r) for r in rows]

    def sincronizar_apelidos(self, catalog) -> int:
        """Make the nicknames follow the model: fill missing product names and disable (never delete) the
        nicknames whose product is gone or has another name. Returns how many were disabled."""
        nomes = {p.id: p.nome for p in catalog}
        desativados = 0
        with self._connect() as db:
            rows = db.execute("select id, produto_id, produto_nome, status from pedido.apelidos").fetchall()
            for row in rows:
                nome = nomes.get(row["produto_id"])
                if nome is None or (row["produto_nome"] is not None and row["produto_nome"] != nome):
                    if row["status"] == "ativo":
                        db.execute("update pedido.apelidos set status = 'desativado', atualizado_em = now() "
                                   "where id = %s", (row["id"],))
                        desativados += 1
                elif row["produto_nome"] is None:
                    db.execute("update pedido.apelidos set produto_nome = %s where id = %s", (nome, row["id"]))
        return desativados

    # -- the order-form models (data-model.md) ---------------------------------------------------
    def salvar_modelo(self, arquivo: str, conteudo: bytes, produtos: int) -> int:
        """Store a model as the next version and make it the active one (the old one is kept)."""
        with self._connect() as db:
            db.execute("select pg_advisory_xact_lock(5005)")
            versao = db.execute("select coalesce(max(versao), 0) + 1 as v from pedido.modelos").fetchone()["v"]
            db.execute("update pedido.modelos set ativo = false where ativo")
            db.execute("insert into pedido.modelos (versao, arquivo, conteudo, produtos, ativo) "
                       "values (%s, %s, %s, %s, true)", (versao, arquivo, conteudo, produtos))
        return versao

    @staticmethod
    def _modelo(row: dict) -> dict:
        row = dict(row)
        row["criado_em"] = _iso(row["criado_em"])
        if "conteudo" in row:
            row["conteudo"] = bytes(row["conteudo"])
        return row

    def versao_ativa(self) -> int | None:
        with self._connect() as db:
            row = db.execute("select versao from pedido.modelos where ativo").fetchone()
        return row["versao"] if row else None

    def modelo_ativo(self) -> dict | None:
        with self._connect() as db:
            row = db.execute("select versao, arquivo, conteudo, produtos, ativo, criado_em "
                             "from pedido.modelos where ativo").fetchone()
        return self._modelo(row) if row else None

    def get_modelo(self, versao: int) -> dict | None:
        with self._connect() as db:
            row = db.execute("select versao, arquivo, conteudo, produtos, ativo, criado_em "
                             "from pedido.modelos where versao = %s", (versao,)).fetchone()
        return self._modelo(row) if row else None

    def listar_modelos(self) -> list[dict]:
        with self._connect() as db:
            rows = db.execute("select versao, arquivo, produtos, ativo, criado_em "
                              "from pedido.modelos order by versao").fetchall()
        return [self._modelo(r) for r in rows]

    # -- the daily message counter (data-model.md) -------------------------------------------------
    def registrar_mensagem(self, conversa: str, dia, limite: int) -> int | None:
        """Count one accepted message of this conversation today. Returns the new count, or None when
        the daily limit was already reached (nothing is counted then)."""
        with self._connect() as db:
            row = db.execute(
                "insert into pedido.uso_diario (conversa, dia, mensagens) values (%s, %s, 1) "
                "on conflict (conversa, dia) do update set mensagens = pedido.uso_diario.mensagens + 1 "
                "where pedido.uso_diario.mensagens < %s returning mensagens", (conversa, dia, limite)).fetchone()
        return row["mensagens"] if row else None

    def atualizar_embedding(self, apelido_id: int, vetor: list[float], modelo: str) -> None:
        """Replace the vector (and the model name) of ONE nickname; its signals and status are untouched."""
        with self._connect() as db:
            db.execute("update pedido.apelidos set embedding = %s, modelo = %s, atualizado_em = now() "
                       "where id = %s", (Vector(vetor), modelo, apelido_id))
