# Imagem do bot de pedidos. Nenhum segredo entra aqui: tudo vem de variáveis de ambiente em tempo de execução.
FROM python:3.11-slim

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    UV_LINK_MODE=copy \
    PATH="/app/.venv/bin:$PATH" \
    ENVIRONMENT=producao

RUN pip install --no-cache-dir "uv==0.12.5" \
    && useradd --create-home --uid 10001 app

WORKDIR /app

# Dependências primeiro (cache de camadas), depois o código.
COPY pyproject.toml uv.lock .python-version ./
RUN uv sync --frozen --no-dev --no-install-project

COPY src ./src
COPY assets ./assets
RUN uv sync --frozen --no-dev \
    && chown -R app:app /app

USER app

# O Render informa a porta em PORT; as migrações rodam antes do deploy: python -m pedido.migrate
EXPOSE 10000
CMD ["python", "-m", "pedido"]
