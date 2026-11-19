"""Test double: a fake OpenAI-compatible chat server (no internet)."""
import asyncio
import hashlib
import json
import socket
import threading
import time

import uvicorn
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse


def vector_for(text: str, dimensions: int, table: dict[str, list[float]] | None = None) -> list[float]:
    """The vector of `text`: from `table` (padded with zeros), otherwise a unit hash vector."""
    if table and text in table:
        given = list(table[text])
        return given + [0.0] * (dimensions - len(given))
    seed = hashlib.sha256(text.encode("utf-8")).digest()
    raw = [(seed[i % len(seed)] - 127.5) for i in range(dimensions)]
    norm = sum(x * x for x in raw) ** 0.5
    return [x / norm for x in raw]


class FakeEmbedder:
    """Stand-in for `pedido.embeddings.Embedder`. `table` maps normalized texts to vectors."""

    def __init__(self, table=None, dimensions: int = 1024, model: str = "fake-embed", fail: bool = False):
        self.table, self.dimensions, self.model, self.fail = dict(table or {}), dimensions, model, fail
        self.calls: list[str] = []

    def embed(self, text: str) -> list[float]:
        self.calls.append(text)
        if self.fail:
            from pedido.embeddings import EmbeddingFailed

            raise EmbeddingFailed("falha simulada")
        return vector_for(text, self.dimensions, self.table)


class FakeOpenAIServer:
    """A tiny OpenAI-style server on a random local port: /v1/chat/completions.

    `requests` records path, authorization header and JSON body; `chat_answers` is a queue of dicts
    returned as the structured answer; `fail_status` makes every call answer with that HTTP status.
    """

    def __init__(self, model: str = "fake-chat", port: int = 0):
        self.requests: list[dict] = []
        self.chat_answers: list[dict] = []
        self.chat_responder = None  # optional: body -> answer dict, used instead of the queue
        self.embed_vectors: dict[str, list[float]] = {}  # text -> vector; others get a hash vector
        self.embed_dimensions = 1024
        self.embed_delay = 0.0  # seconds to wait before answering an embeddings call
        self.embed_fail_status: int | None = None  # HTTP status for embeddings calls only

        self.fail_status: int | None = None
        self.model = model
        self._server: uvicorn.Server | None = None
        self._thread: threading.Thread | None = None
        self.port = port
        self.app = self._build_app()

    @property
    def base_url(self) -> str:
        return f"http://127.0.0.1:{self.port}/v1"

    def _build_app(self) -> FastAPI:
        app = FastAPI()

        async def record(request: Request) -> dict:
            body = await request.json()
            self.requests.append({"path": request.url.path,
                                  "authorization": request.headers.get("authorization"), "json": body})
            return body

        def failure(status=None):
            return JSONResponse({"error": {"message": "falha simulada", "type": "server_error"}},
                                status_code=status or self.fail_status)

        @app.post("/v1/chat/completions")
        async def chat(request: Request):
            body = await record(request)
            if self.fail_status:
                return failure()
            if self.chat_responder is not None:
                answer = json.dumps(self.chat_responder(body))
            else:
                answer = json.dumps(self.chat_answers.pop(0) if self.chat_answers else {})
            tools = body.get("tools")
            if tools:
                message = {"role": "assistant", "content": None, "refusal": None, "tool_calls": [{
                    "id": "call_1", "type": "function",
                    "function": {"name": tools[0]["function"]["name"], "arguments": answer}}]}
                finish = "tool_calls"
            else:
                message = {"role": "assistant", "content": answer, "refusal": None}
                finish = "stop"
            return {"id": "chatcmpl-fake", "object": "chat.completion", "created": 0,
                    "model": body.get("model", self.model),
                    "choices": [{"index": 0, "message": message, "finish_reason": finish}],
                    "usage": {"prompt_tokens": 1, "completion_tokens": 1, "total_tokens": 2}}

        @app.post("/v1/embeddings")
        async def embeddings(request: Request):
            body = await record(request)
            if self.embed_delay:
                await asyncio.sleep(self.embed_delay)
            if self.fail_status or self.embed_fail_status:
                return failure(self.embed_fail_status or self.fail_status)
            texts = body["input"] if isinstance(body["input"], list) else [body["input"]]
            data = [{"object": "embedding", "index": i,
                     "embedding": vector_for(t, self.embed_dimensions, self.embed_vectors)}
                    for i, t in enumerate(texts)]
            return {"object": "list", "data": data, "model": body.get("model", self.model),
                    "usage": {"prompt_tokens": 1, "total_tokens": 1}}

        return app

    def __enter__(self):
        if not self.port:
            with socket.socket() as s:
                s.bind(("127.0.0.1", 0))
                self.port = s.getsockname()[1]
        self._server = uvicorn.Server(uvicorn.Config(self.app, host="127.0.0.1", port=self.port,
                                                     log_level="error"))
        self._thread = threading.Thread(target=self._server.run, daemon=True)
        self._thread.start()
        deadline = time.time() + 10
        while not self._server.started and time.time() < deadline:
            time.sleep(0.02)
        return self

    def __exit__(self, *exc):
        self._server.should_exit = True
        self._thread.join(timeout=5)


class InlineExecutor:
    """Runs the submitted work immediately, in the caller's thread (deterministic tests)."""

    def submit(self, fn, *args, **kwargs):
        fn(*args, **kwargs)


class DeferredExecutor:
    """Collects the submitted work; `run()` executes it later (to prove it happens after the reply)."""

    def __init__(self):
        self.pending = []

    def submit(self, fn, *args, **kwargs):
        self.pending.append((fn, args, kwargs))

    def run(self):
        work, self.pending = self.pending, []
        for fn, args, kwargs in work:
            fn(*args, **kwargs)
