#!/usr/bin/env bash
set -Eeuo pipefail
IFS=$'\n\t'

ROOT="$(git rev-parse --show-toplevel 2>/dev/null || pwd)"
cd "$ROOT"

echo "== Git diff integrity =="
git diff --check

echo "== Canonical planning paths =="
python3 - <<'PY'
from pathlib import Path

root = Path("circuits/spa-francorchamps/seasons/2026")
required = [
    root / "specs/2026-07-14-calibration-design.md",
    root / "reviews/2026-07-15-calibration-review-recommendations.md",
    root / "reviews/2026-07-15-calibration-review-defence.md",
    root / "reviews/2026-07-15-plan-reconciliation.md",
    root / "plans/2026-07-14-spa-calibration-program.md",
    root / "plans/2026-07-14-spa-calibration-data-pipeline.md",
    root / "plans/2026-07-14-spa-calibration-model-prediction.md",
    root / "plans/2026-07-14-spa-calibration-app-integration.md",
    root / "plans/2026-07-15-pr1-closeout-plan.md",
    root / "project/README.md",
    root / "project/STATUS.md",
    root / "project/ACTIVITY.md",
    root / "project/DECISIONS.md",
    root / "project/LESSONS.md",
]
missing = [str(path) for path in required if not path.is_file()]
if missing:
    raise SystemExit("missing canonical files:\n" + "\n".join(missing))

plans = list((root / "plans").glob("*.md"))
stale = []
for path in plans:
    text = path.read_text(encoding="utf-8")
    if "docs/superpowers/plans/2026-07-14-spa-calibration" in text:
        stale.append(str(path))
if stale:
    raise SystemExit("stale moved plan references:\n" + "\n".join(stale))
print(f"validated {len(required)} canonical files and {len(plans)} plan path(s)")
PY

echo "== Project-control records =="
python3 scripts/verify_project_control.py

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
    ["git", "ls-files", "*.json"], check=True, capture_output=True, text=True
).stdout.splitlines()
for filename in tracked:
    with Path(filename).open(encoding="utf-8") as handle:
        json.load(handle)
print(f"validated {len(tracked)} JSON file(s)")
PY

echo "== Python =="
python_files=()
while IFS= read -r -d '' file; do
  python_files+=("$file")
done < <(git ls-files -z '*.py')
while IFS= read -r -d '' file; do
  python_files+=("$file")
done < <(git ls-files -z --others --exclude-standard '*.py')
if ((${#python_files[@]})); then
  mapfile -t python_files < <(printf '%s\n' "${python_files[@]}" | sort -u)
  pycache_dir="$(mktemp -d)"
  PYTHONPYCACHEPREFIX="$pycache_dir" python3 -m compileall -q "${python_files[@]}"
  rm -rf "$pycache_dir"

  if command -v ruff >/dev/null 2>&1; then
    if [[ "${RACE_LAB_FULL_LINT:-0}" == "1" ]]; then
      echo "running repository-wide Ruff audit"
      ruff check .
    else
      base=""
      for candidate in origin/main main; do
        if git rev-parse --verify "$candidate" >/dev/null 2>&1; then
          base="$(git merge-base HEAD "$candidate")"
          break
        fi
      done

      declare -a lint_targets=()
      for directory in calibration tests scripts; do
        if [[ -d "$directory" ]]; then
          while IFS= read -r -d '' file; do lint_targets+=("$file"); done < <(find "$directory" -type f -name '*.py' -print0)
        fi
      done
      if [[ -n "$base" ]]; then
        while IFS= read -r file; do
          [[ -f "$file" ]] && lint_targets+=("$file")
        done < <(git diff --name-only --diff-filter=ACMR "$base"...HEAD -- '*.py')
      fi
      while IFS= read -r file; do
        [[ -f "$file" ]] && lint_targets+=("$file")
      done < <(git diff --name-only --diff-filter=ACMR HEAD -- '*.py')
      while IFS= read -r file; do
        [[ -f "$file" ]] && lint_targets+=("$file")
      done < <(git ls-files --others --exclude-standard '*.py')

      if ((${#lint_targets[@]})); then
        mapfile -t lint_targets < <(printf '%s\n' "${lint_targets[@]}" | sort -u)
        ruff check "${lint_targets[@]}"
      else
        echo "no calibration/test/script or changed Python files to lint"
      fi
      echo "set RACE_LAB_FULL_LINT=1 to run the explicit repository-wide legacy-debt audit"
    fi
  else
    echo "ruff not installed; skipped"
  fi

  if command -v pytest >/dev/null 2>&1 && [[ -d tests ]]; then
    pytest -q
  else
    python3 -m unittest discover -s tests -p 'test_*.py' -v
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
