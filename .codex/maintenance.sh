#!/usr/bin/env bash
set -Eeuo pipefail
IFS=$'\n\t'

ROOT="$(git rev-parse --show-toplevel 2>/dev/null || pwd)"
cd "$ROOT"

if [[ -f requirements-dev.txt ]]; then
  python3 -m pip install --disable-pip-version-check -r requirements-dev.txt
fi

if [[ -f pyproject.toml ]]; then
  python3 -m pip install --disable-pip-version-check -e '.[dev]' \
    || python3 -m pip install --disable-pip-version-check -e .
fi

if [[ -f pnpm-lock.yaml ]]; then
  corepack enable
  pnpm install --frozen-lockfile
elif [[ -f yarn.lock ]]; then
  corepack enable
  yarn install --immutable || yarn install --frozen-lockfile
elif [[ -f package-lock.json ]]; then
  npm ci
elif [[ -f package.json ]]; then
  npm install
fi
