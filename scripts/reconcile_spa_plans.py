#!/usr/bin/env python3
from __future__ import annotations

import base64
import gzip
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PAYLOAD = ROOT / ".automation"
PLAN_ROOT = ROOT / "circuits/spa-francorchamps/seasons/2026"


def read_encoded(name: str) -> str:
    direct = PAYLOAD / name
    if direct.exists():
        return direct.read_text().strip()
    chunks = sorted(PAYLOAD.glob(f"{name}.part-*"))
    if not chunks:
        raise FileNotFoundError(name)
    return "".join(chunk.read_text().strip() for chunk in chunks)


def decode(name: str) -> bytes:
    return gzip.decompress(base64.b64decode(read_encoded(name)))


def run(*args: str) -> None:
    subprocess.run(args, cwd=ROOT, check=True)


patch_path = PAYLOAD / "spa-plans.patch"
patch_path.write_bytes(decode("spa-plans.patch.gz.b64"))
run("git", "apply", "--check", str(patch_path))
run("git", "apply", str(patch_path))

reconciliation = PLAN_ROOT / "reviews/2026-07-15-plan-reconciliation.md"
reconciliation.parent.mkdir(parents=True, exist_ok=True)
reconciliation.write_bytes(decode("reconciliation.md.gz.b64"))

verify = ROOT / "scripts/verify.sh"
verify.write_bytes(decode("verify.sh.gz.b64"))
verify.chmod(0o755)

required = {
    PLAN_ROOT / "plans/2026-07-14-spa-calibration-program.md": [
        "spa-2026-dry-qualifying-reference/v1",
        "rolling-origin",
        "correction ownership ledger",
    ],
    PLAN_ROOT / "plans/2026-07-14-spa-calibration-data-pipeline.md": [
        "CircuitYearEligibility",
        "raw coverage",
        "fallback_reason",
        "braking_onset_from_complex_start_m",
    ],
    PLAN_ROOT / "plans/2026-07-14-spa-calibration-model-prediction.md": [
        "rolling-origin",
        "weighted interval score",
        "residual covariance",
        "battery_reserve_kj",
        "recompute",
    ],
    PLAN_ROOT / "plans/2026-07-14-spa-calibration-app-integration.md": [
        "validateCalibrationArtifact",
        "normalizeOpenF1Trace",
        "identical release validation",
    ],
    reconciliation: [
        "## A. Independent review requirements",
        "## B. Codex review findings",
        "B24",
    ],
}
for path, needles in required.items():
    text = path.read_text(encoding="utf-8")
    for needle in needles:
        if needle.lower() not in text.lower():
            raise SystemExit(f"{path}: missing required reconciliation term: {needle}")

print("Spa calibration plans reconciled")
