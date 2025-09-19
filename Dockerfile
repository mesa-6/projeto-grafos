FROM python:3.12-slim

# Variáveis de ambiente
ENV POETRY_VERSION=2.1.4 \
    POETRY_VIRTUALENVS_CREATE=false \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PATH="/home/dev/.local/bin:$PATH" \
    REPO_URL="https://github.com/ArthurCapistrano/projeto-grafos.git" \
    REPO_BRANCH="main" \
    REPO_DIR="/projeto-grafos" \
    START_CMD="python -m src.main"

# criar usuário não-root
ARG UNAME=dev
ARG UID=1000
RUN groupadd -g ${UID} ${UNAME} || true && \
    useradd --create-home --uid ${UID} --gid ${UID} ${UNAME}

WORKDIR /opt/app

# instalar dependências do sistema e poetry via pip (mais previsível para todos os usuários)
RUN apt-get update && \
    apt-get install -y --no-install-recommends git ca-certificates build-essential curl && \
    python -m pip install --upgrade pip && \
    pip install "poetry==${POETRY_VERSION}" && \
    apt-get purge -y curl && apt-get clean && rm -rf /var/lib/apt/lists/*

# copiar apenas o pyproject/poetry.lock para aproveitar cache de camada
COPY pyproject.toml poetry.lock /opt/app/

# instalar dependências python (poetry vai instalar no ambiente do container, não cria venv)
RUN poetry install --no-root --no-interaction

# criar diretório onde o repo será clonado e ajustar permissões para o usuário dev
RUN mkdir -p ${REPO_DIR} && chown -R ${UNAME}:${UNAME} ${REPO_DIR}

# copiar entrypoint e garantir execução
COPY entrypoint.sh /usr/local/bin/entrypoint.sh
RUN chmod +x /usr/local/bin/entrypoint.sh

# expor porta (ajuste se necessário)
EXPOSE 8000

# usar o usuário não-root para rodar o app (evita arquivos root no host)
USER ${UNAME}

# entrypoint fará git clone/pull e então executará o comando definido em START_CMD
ENTRYPOINT ["/usr/local/bin/entrypoint.sh"]
CMD ["sh", "-c", "${START_CMD}"]
