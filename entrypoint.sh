#!/usr/bin/env bash
set -e

# se o diretório não existe, clona; caso exista, faz pull
if [ ! -d "$REPO_DIR/.git" ]; then
  echo "Clonando repo $REPO_URL (branch $REPO_BRANCH) em $REPO_DIR..."
  git clone --depth 1 --branch "$REPO_BRANCH" "$REPO_URL" "$REPO_DIR"
else
  echo "Repositório já existe em $REPO_DIR — atualizando (git pull)..."
  cd "$REPO_DIR"
  git fetch origin "$REPO_BRANCH"
  git reset --hard "origin/$REPO_BRANCH"
fi

# mudar para o diretório do projeto
cd "$REPO_DIR"

# opcional: caso precise instalar algo dinâmico (ex.: editable)
# pip install -e .

# executar comando de start (default: env START_CMD)
exec /bin/sh -lc "$*"
