#!/usr/bin/env bash
set -euo pipefail

# Variáveis (recebem do ENV do container)
REPO_URL="${REPO_URL:-}"
REPO_BRANCH="${REPO_BRANCH:-main}"
REPO_DIR="${REPO_DIR:-/projeto-grafos}"
START_CMD="${START_CMD:-python -m src.main}"

# Se repository não existir, clona; se existir, faz reset hard para branch remoto
if [ ! -d "${REPO_DIR}/.git" ]; then
  echo "Clonando ${REPO_URL} (branch ${REPO_BRANCH}) em ${REPO_DIR}..."
  git clone --depth 1 --branch "${REPO_BRANCH}" "${REPO_URL}" "${REPO_DIR}"
else
  echo "Repositório já existe em ${REPO_DIR} — atualizando..."
  cd "${REPO_DIR}"
  git fetch origin "${REPO_BRANCH}"
  git reset --hard "origin/${REPO_BRANCH}"
fi

# garantir que o usuário atual consiga escrever (por precaução)
chown -R "$(id -u):$(id -g)" "${REPO_DIR}" || true

# entrar no diretório do projeto
cd "${REPO_DIR}"

# Executar o comando final (START_CMD). Usamos exec para substituir o processo shell.
echo "Executando: ${START_CMD}"
exec /bin/sh -lc "${START_CMD}"
