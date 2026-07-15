#!/usr/bin/env bash
set -Eeuo pipefail
IFS=$'\n\t'

ROOT="$(git rev-parse --show-toplevel)"
cd "$ROOT"

echo "== Git diff integrity =="
git diff --check

echo "== Shell syntax =="
shell_files=()
while IFS= read -r -d '' file; do
  shell_files+=("$file")
done < <(git ls-files -z '*.sh')

if ((${#shell_files[@]})); then
  for file in "${shell_files[@]}"; do
    bash -n "$file"
  done

  if command -v shellcheck >/dev/null 2>&1; then
    shellcheck "${shell_files[@]}"
  else
    echo "shellcheck not installed; skipped"
  fi
fi

echo "== Structured-file syntax =="
python3 - <<'PY'
from __future__ import annotations

import json
import subprocess
from pathlib import Path

tracked = subprocess.run(
    ["git", "ls-files", "*.json"],
    check=True,
    capture_output=True,
    text=True,
).stdout.splitlines()

for filename in tracked:
    path = Path(filename)
    with path.open(encoding="utf-8") as handle:
        json.load(handle)

print(f"validated {len(tracked)} JSON file(s)")
PY

echo "== Python =="
python_files=()
while IFS= read -r -d '' file; do
  python_files+=("$file")
done < <(git ls-files -z '*.py')

if ((${#python_files[@]})); then
  python3 -m compileall -q "${python_files[@]}"

  if command -v ruff >/dev/null 2>&1; then
    ruff check .
  else
    echo "ruff not installed; skipped"
  fi

  if command -v pytest >/dev/null 2>&1 && [[ -d tests ]]; then
    pytest -q
  fi
fi

echo "== Node =="
if [[ -f package.json ]]; then
  node -e "JSON.parse(require('node:fs').readFileSync('package.json', 'utf8'))"

  run_npm_script() {
    local script="$1"
    if node -e "const p=require('./package.json'); process.exit(p.scripts?.['$script'] ? 0 : 1)"; then
      npm run "$script"
    fi
  }

  run_npm_script lint
  run_npm_script typecheck
  run_npm_script test
  run_npm_script build
fi

echo "Verification complete."
