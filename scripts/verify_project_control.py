#!/usr/bin/env python3
"""Validate Spa 2026 project-control records and maintenance coupling."""

from __future__ import annotations

import os
import re
import subprocess
import sys
from datetime import datetime
from pathlib import Path
from typing import Iterable


SPA_ROOT = Path("circuits/spa-francorchamps/seasons/2026")
PROJECT_ROOT = SPA_ROOT / "project"
PLAN_PATH = SPA_ROOT / "plans/2026-07-15-pr1-closeout-plan.md"
REQUIRED_FILES = {
    PROJECT_ROOT / "README.md": "race-lab-project-maintenance/v1",
    PROJECT_ROOT / "STATUS.md": "race-lab-project-status/v1",
    PROJECT_ROOT / "ACTIVITY.md": "race-lab-project-activity/v1",
    PROJECT_ROOT / "DECISIONS.md": "race-lab-project-decisions/v1",
    PROJECT_ROOT / "LESSONS.md": "race-lab-project-lessons/v1",
    PLAN_PATH: "race-lab-closeout-plan/v1",
}
STATUS_REQUIRED_KEYS = {
    "schema",
    "initiative",
    "phase",
    "repository",
    "branch",
    "pull_request",
    "last_observed_remote_head",
    "last_observed_at",
    "evidence_source",
    "publication_state",
    "verification_state",
    "active_tasks",
    "next_action",
    "original_comments_total",
    "original_comments_rated",
    "original_comments_replied",
    "original_comments_resolved",
    "fresh_comments_total",
    "fresh_comments_rated",
    "fresh_comments_replied",
    "fresh_comments_resolved",
}
ACTIVITY_FIELDS = (
    "Evidence status",
    "Starting state",
    "Work performed",
    "Files changed",
    "Verification",
    "Publication / remote actions",
    "Result",
    "Next action",
    "Lessons review",
)
PLACEHOLDER_PATTERN = re.compile(
    r"\b(?:TBD|TODO|FIXME|fill in details|implement later)\b", re.IGNORECASE
)
ID_PATTERNS = {
    "activity": re.compile(r"^## (A-\d{3}) — ([^—\n]+) — ", re.MULTILINE),
    "decision": re.compile(r"^## (D-\d{3}) — ", re.MULTILINE),
    "lesson": re.compile(r"^## (L-\d{3}) — ", re.MULTILINE),
    "task": re.compile(r"^### ([A-Z]+-\d{2}) — ", re.MULTILINE),
}


class ValidationError(RuntimeError):
    """Raised when project-control records violate their contract."""


class TaskState:
    def __init__(self, task_id: str, completed: bool) -> None:
        self.task_id = task_id
        self.completed = completed


def _parse_scalar(value: str) -> object:
    value = value.strip()
    if value.startswith("[") and value.endswith("]"):
        inner = value[1:-1].strip()
        if not inner:
            return []
        return [item.strip().strip("'\"") for item in inner.split(",")]
    if re.fullmatch(r"-?\d+", value):
        return int(value)
    if value.lower() in {"true", "false"}:
        return value.lower() == "true"
    return value.strip("'\"")


def parse_front_matter(text: str, path: Path | str = "<memory>") -> dict[str, object]:
    lines = text.splitlines()
    if not lines or lines[0].strip() != "---":
        raise ValidationError(f"{path}: missing YAML front matter")
    try:
        closing = lines.index("---", 1)
    except ValueError as exc:
        raise ValidationError(f"{path}: unterminated YAML front matter") from exc
    result: dict[str, object] = {}
    for line in lines[1:closing]:
        if not line.strip() or line.lstrip().startswith("#"):
            continue
        if ":" not in line:
            raise ValidationError(f"{path}: malformed front-matter line: {line}")
        key, raw = line.split(":", 1)
        key = key.strip()
        if not key:
            raise ValidationError(f"{path}: empty front-matter key")
        if key in result:
            raise ValidationError(f"{path}: duplicate front-matter key {key}")
        result[key] = _parse_scalar(raw)
    return result


def _read(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8")
    except FileNotFoundError as exc:
        raise ValidationError(f"missing required project-control file: {path}") from exc


def _unique_ids(text: str, pattern: re.Pattern[str], label: str) -> list[str]:
    ids = [match.group(1) for match in pattern.finditer(text)]
    seen: set[str] = set()
    for item in ids:
        if item in seen:
            raise ValidationError(f"duplicate {label} ID {item}")
        seen.add(item)
    if not ids:
        raise ValidationError(f"no {label} IDs found")
    return ids


def _parse_datetime(value: str, label: str) -> datetime:
    normalized = value.strip().replace("Z", "+00:00")
    try:
        parsed = datetime.fromisoformat(normalized)
    except ValueError as exc:
        raise ValidationError(f"invalid ISO-8601 timestamp for {label}: {value}") from exc
    if parsed.tzinfo is None:
        raise ValidationError(f"timestamp must include a timezone for {label}: {value}")
    return parsed


def parse_tasks(plan_text: str) -> dict[str, TaskState]:
    matches = list(ID_PATTERNS["task"].finditer(plan_text))
    if not matches:
        raise ValidationError("active closeout plan contains no stable task IDs")
    tasks: dict[str, TaskState] = {}
    for index, match in enumerate(matches):
        task_id = match.group(1)
        if task_id in tasks:
            raise ValidationError(f"duplicate task ID {task_id}")
        end = matches[index + 1].start() if index + 1 < len(matches) else len(plan_text)
        section = plan_text[match.start() : end]
        checkboxes = re.findall(r"^- \[([ xX])\]", section, re.MULTILINE)
        completed = bool(checkboxes) and all(mark.lower() == "x" for mark in checkboxes)
        tasks[task_id] = TaskState(task_id=task_id, completed=completed)
    return tasks


def validate_status(status_text: str, plan_text: str) -> None:
    metadata = parse_front_matter(status_text, PROJECT_ROOT / "STATUS.md")
    missing = sorted(STATUS_REQUIRED_KEYS - metadata.keys())
    if missing:
        raise ValidationError("STATUS.md missing required fields: " + ", ".join(missing))
    if metadata["schema"] != "race-lab-project-status/v1":
        raise ValidationError("STATUS.md has unsupported schema")
    if metadata["initiative"] != "spa-2026-calibration":
        raise ValidationError("STATUS.md has the wrong initiative")
    if not re.fullmatch(r"[0-9a-f]{40}", str(metadata["last_observed_remote_head"])):
        raise ValidationError("STATUS.md last_observed_remote_head must be a 40-character SHA")
    _parse_datetime(str(metadata["last_observed_at"]), "last_observed_at")
    if not str(metadata["next_action"]).strip():
        raise ValidationError("STATUS.md next_action must be non-empty")

    tasks = parse_tasks(plan_text)
    active_tasks = metadata["active_tasks"]
    if not isinstance(active_tasks, list) or not active_tasks:
        raise ValidationError("STATUS.md active_tasks must be a non-empty list")
    for task_id in active_tasks:
        task_id = str(task_id)
        if task_id not in tasks:
            raise ValidationError(f"STATUS.md references unknown active task {task_id}")
        if tasks[task_id].completed:
            raise ValidationError(f"STATUS.md lists completed task {task_id} as active")

    for prefix in ("original", "fresh"):
        total_key = f"{prefix}_comments_total"
        total = metadata[total_key]
        if not isinstance(total, int) or total < 0:
            raise ValidationError(f"{total_key} must be a non-negative integer")
        for action in ("rated", "replied", "resolved"):
            key = f"{prefix}_comments_{action}"
            count = metadata[key]
            if not isinstance(count, int) or count < 0 or count > total:
                raise ValidationError(f"{key} must be between 0 and {total}")


def _entry_sections(text: str, pattern: re.Pattern[str]) -> list[tuple[re.Match[str], str]]:
    matches = list(pattern.finditer(text))
    sections: list[tuple[re.Match[str], str]] = []
    for index, match in enumerate(matches):
        end = matches[index + 1].start() if index + 1 < len(matches) else len(text)
        sections.append((match, text[match.start() : end]))
    return sections


def validate_activity(activity_text: str) -> None:
    _unique_ids(activity_text, ID_PATTERNS["activity"], "activity")
    previous: datetime | None = None
    for match, section in _entry_sections(activity_text, ID_PATTERNS["activity"]):
        entry_id = match.group(1)
        timestamp = _parse_datetime(match.group(2).strip(), entry_id)
        if previous is not None and timestamp < previous:
            raise ValidationError(f"activity timestamps are not monotonic at {entry_id}")
        previous = timestamp
        for field in ACTIVITY_FIELDS:
            if not re.search(rf"^\*\*{re.escape(field)}:\*\*\s*\S", section, re.MULTILINE):
                raise ValidationError(f"{entry_id} missing required field {field}")


def validate_registers(decisions_text: str, lessons_text: str) -> None:
    _unique_ids(decisions_text, ID_PATTERNS["decision"], "decision")
    _unique_ids(lessons_text, ID_PATTERNS["lesson"], "lesson")


def ensure_append_only(old_text: str, new_text: str) -> None:
    if not new_text.startswith(old_text):
        raise ValidationError("ACTIVITY.md violates append-only history; append a correction entry instead")


def _current_activity_entry(activity_text: str) -> str:
    entries = _entry_sections(activity_text, ID_PATTERNS["activity"])
    return entries[-1][1] if entries else activity_text


def validate_required_record_updates(
    changed_files: Iterable[str], *, activity_text: str = ""
) -> None:
    changed = {str(Path(path)) for path in changed_files}
    if not changed:
        return
    prefix = str(SPA_ROOT) + "/"
    status = str(PROJECT_ROOT / "STATUS.md")
    activity = str(PROJECT_ROOT / "ACTIVITY.md")
    decisions = str(PROJECT_ROOT / "DECISIONS.md")
    lessons = str(PROJECT_ROOT / "LESSONS.md")
    readme = str(PROJECT_ROOT / "README.md")

    material = {
        path
        for path in changed
        if path.startswith(prefix)
        and any(f"/{part}/" in path for part in ("plans", "specs", "reviews"))
    }
    enforcement = {
        path
        for path in changed
        if path in {"AGENTS.md", "scripts/verify.sh", "scripts/verify_project_control.py", ".github/workflows/verify.yml"}
    }
    if material or enforcement:
        missing = [path for path in (status, activity) if path not in changed]
        if missing:
            raise ValidationError(
                "material Spa or enforcement changes require updates to " + ", ".join(missing)
            )
    if any("/specs/" in path for path in changed) and decisions not in changed:
        raise ValidationError("Spa specification changes require DECISIONS.md")
    if any("/reviews/" in path for path in changed):
        no_new_lesson = bool(
            re.search(
                r"(?:Lessons review:\*\*\s*no-new-lesson|lessons_reviewed:\s*no-new-lesson)",
                _current_activity_entry(activity_text),
                re.IGNORECASE,
            )
        )
        if lessons not in changed and not no_new_lesson:
            raise ValidationError(
                "review reconciliation requires LESSONS.md or an explicit lessons_reviewed: no-new-lesson activity note"
            )
    if status in changed and activity not in changed:
        raise ValidationError("STATUS.md changes require ACTIVITY.md")
    if enforcement and readme not in changed:
        raise ValidationError("project-control enforcement changes require project/README.md review")


def _git_output(root: Path, args: list[str]) -> str | None:
    try:
        return subprocess.run(
            ["git", *args], cwd=root, check=True, capture_output=True, text=True
        ).stdout.strip()
    except (subprocess.CalledProcessError, FileNotFoundError):
        return None


def discover_base_ref(root: Path) -> str | None:
    explicit = os.environ.get("RACE_LAB_BASE_REF")
    candidates = [explicit] if explicit else []
    candidates.extend(["origin/main", "main"])
    for candidate in candidates:
        if candidate and _git_output(root, ["rev-parse", "--verify", candidate]):
            return candidate
    return None


def discover_changed_files(root: Path, base_ref: str | None = None) -> set[str]:
    changed: set[str] = set()
    base_ref = base_ref or discover_base_ref(root)
    if base_ref:
        output = _git_output(root, ["diff", "--name-only", "--diff-filter=ACMR", f"{base_ref}...HEAD"])
        if output:
            changed.update(output.splitlines())
    for args in (
        ["diff", "--name-only", "--diff-filter=ACMR", "HEAD"],
        ["ls-files", "--others", "--exclude-standard"],
    ):
        output = _git_output(root, args)
        if output:
            changed.update(output.splitlines())
    return changed


def _base_activity(root: Path, base_ref: str | None) -> str | None:
    if not base_ref:
        return None
    path = str(PROJECT_ROOT / "ACTIVITY.md")
    return _git_output(root, ["show", f"{base_ref}:{path}"])


def validate_project(
    root: Path, *, changed_files: Iterable[str] | None = None, base_ref: str | None = None
) -> None:
    root = root.resolve()
    texts: dict[Path, str] = {}
    for relative, schema in REQUIRED_FILES.items():
        text = _read(root / relative)
        metadata = parse_front_matter(text, relative)
        if metadata.get("schema") != schema:
            raise ValidationError(f"{relative}: expected schema {schema}")
        if metadata.get("initiative") != "spa-2026-calibration":
            raise ValidationError(f"{relative}: wrong initiative")
        if PLACEHOLDER_PATTERN.search(text):
            raise ValidationError(f"{relative}: contains an unresolved placeholder")
        texts[relative] = text

    validate_status(texts[PROJECT_ROOT / "STATUS.md"], texts[PLAN_PATH])
    validate_activity(texts[PROJECT_ROOT / "ACTIVITY.md"])
    validate_registers(
        texts[PROJECT_ROOT / "DECISIONS.md"], texts[PROJECT_ROOT / "LESSONS.md"]
    )

    resolved_base = base_ref or discover_base_ref(root)
    previous_activity = _base_activity(root, resolved_base)
    if previous_activity is not None:
        ensure_append_only(previous_activity, texts[PROJECT_ROOT / "ACTIVITY.md"])

    actual_changed = (
        set(changed_files) if changed_files is not None else discover_changed_files(root, resolved_base)
    )
    validate_required_record_updates(
        actual_changed, activity_text=texts[PROJECT_ROOT / "ACTIVITY.md"]
    )


def main() -> int:
    root = Path(_git_output(Path.cwd(), ["rev-parse", "--show-toplevel"]) or Path.cwd())
    try:
        validate_project(root)
    except ValidationError as exc:
        print(f"project-control validation failed: {exc}", file=sys.stderr)
        return 1
    print("validated Spa 2026 project-control records")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
