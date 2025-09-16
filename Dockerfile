FROM python:3.12-slim

ENV POETRY_VERSION=2.1.4 \
    POETRY_VIRTUALENVS_CREATE=false \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PATH="/root/.local/bin:$PATH" \
    REPO_DIR=/projeto-grafos

WORKDIR /opt/app

# instalar dependências do sistema (git para clonar em runtime)
RUN apt-get update && \
    apt-get install -y --no-install-recommends git curl ca-certificates build-essential && \
    curl -sSL https://install.python-poetry.org | python3 - && \
    apt-get purge -y curl && \
    apt-get clean && rm -rf /var/lib/apt/lists/*

# copiar só pyproject/poetry.lock para instalar deps (cache layer)
COPY pyproject.toml poetry.lock /opt/app/

# instalar dependências python (no ambiente do container, sem virtualenvs)
RUN poetry install --no-root

# copiar util scripts
COPY entrypoint.sh /usr/local/bin/entrypoint.sh
RUN chmod +x /usr/local/bin/entrypoint.sh

# Porta padrão (ajuste conforme app: 8000 no docker-compose que você tinha)
EXPOSE 8000

# Quando o container iniciar, o entrypoint fará clone/pull e depois executará START_CMD
# START_CMD deve ser algo como "python -m src.main" ou "uvicorn src.app:app --host 0.0.0.0 --port 8000"
ENV REPO_URL=https://github.com/ArthurCapistrano/projeto-grafos.git
ENV REPO_BRANCH=main
ENV REPO_DIR=/projeto-grafos
ENV START_CMD="python -m src.main"

ENTRYPOINT ["entrypoint.sh"]
CMD ["sh", "-c", "${START_CMD}"]
