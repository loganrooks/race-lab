from __future__ import annotations

import importlib.util
import tempfile
import unittest
from pathlib import Path


MODULE_PATH = Path(__file__).parents[1] / "scripts" / "verify_project_control.py"
spec = importlib.util.spec_from_file_location("verify_project_control", MODULE_PATH)
if spec is None or spec.loader is None:
    raise RuntimeError("unable to load project-control validator")
validator = importlib.util.module_from_spec(spec)
spec.loader.exec_module(validator)


class ProjectControlValidationTests(unittest.TestCase):
    def make_project(self) -> Path:
        temp = tempfile.TemporaryDirectory()
        self.addCleanup(temp.cleanup)
        root = Path(temp.name)
        project = root / "circuits/spa-francorchamps/seasons/2026/project"
        plans = project.parent / "plans"
        project.mkdir(parents=True)
        plans.mkdir(parents=True)

        (plans / "2026-07-15-pr1-closeout-plan.md").write_text(
            """---
schema: race-lab-closeout-plan/v1
initiative: spa-2026-calibration
---
# Plan
### TASK-01 — Active task
- [ ] work
### TASK-02 — Completed task
- [x] done
""",
            encoding="utf-8",
        )
        (project / "README.md").write_text(
            """---
schema: race-lab-project-maintenance/v1
initiative: spa-2026-calibration
---
# Maintenance
""",
            encoding="utf-8",
        )
        (project / "STATUS.md").write_text(
            """---
schema: race-lab-project-status/v1
initiative: spa-2026-calibration
phase: closeout
repository: loganrooks/race-lab
branch: test
pull_request: 1
last_observed_remote_head: 1111111111111111111111111111111111111111
last_observed_at: 2026-07-15T22:12:44Z
evidence_source: test
publication_state: local
verification_state: pending
active_tasks: [TASK-01]
next_action: Do TASK-01.
original_comments_total: 23
original_comments_rated: 5
original_comments_replied: 0
original_comments_resolved: 23
fresh_comments_total: 12
fresh_comments_rated: 0
fresh_comments_replied: 0
fresh_comments_resolved: 0
---
# Status
""",
            encoding="utf-8",
        )
        (project / "ACTIVITY.md").write_text(
            """---
schema: race-lab-project-activity/v1
initiative: spa-2026-calibration
mutation: append-only
---
# Activity
## A-001 — 2026-07-15T20:00:00Z — Test
**Evidence status:** locally-verified.
**Starting state:** start.
**Work performed:** work.
**Files changed:** file.
**Verification:** verified.
**Publication / remote actions:** none.
**Result:** result.
**Next action:** next.
**Lessons review:** no-new-lesson.
""",
            encoding="utf-8",
        )
        (project / "DECISIONS.md").write_text(
            """---
schema: race-lab-project-decisions/v1
initiative: spa-2026-calibration
---
# Decisions
## D-001 — Accepted — Test
**Decision:** test.
**Rationale:** test.
**Rejected alternatives:** none.
**Affected interfaces:** none.
**Reversal conditions:** explicit change.
""",
            encoding="utf-8",
        )
        (project / "LESSONS.md").write_text(
            """---
schema: race-lab-project-lessons/v1
initiative: spa-2026-calibration
---
# Lessons
## L-001 — Active — Test
**Friction:** test.
**Systemic cause:** test.
**Consequence:** test.
**Guardrail:** test.
**Enforcement:** test.
**Evidence of effectiveness:** pending.
""",
            encoding="utf-8",
        )
        return root

    def test_valid_project_records_pass(self) -> None:
        root = self.make_project()
        validator.validate_project(root, changed_files=[])

    def test_active_task_must_exist_and_be_incomplete(self) -> None:
        root = self.make_project()
        status = root / "circuits/spa-francorchamps/seasons/2026/project/STATUS.md"
        status.write_text(status.read_text().replace("[TASK-01]", "[TASK-02]"))
        with self.assertRaisesRegex(validator.ValidationError, "completed task"):
            validator.validate_project(root, changed_files=[])

    def test_review_counters_cannot_exceed_total(self) -> None:
        root = self.make_project()
        status = root / "circuits/spa-francorchamps/seasons/2026/project/STATUS.md"
        status.write_text(status.read_text().replace("fresh_comments_rated: 0", "fresh_comments_rated: 13"))
        with self.assertRaisesRegex(validator.ValidationError, "fresh_comments_rated"):
            validator.validate_project(root, changed_files=[])

    def test_duplicate_lesson_ids_fail(self) -> None:
        root = self.make_project()
        lessons = root / "circuits/spa-francorchamps/seasons/2026/project/LESSONS.md"
        lessons.write_text(lessons.read_text() + "\n## L-001 — Active — Duplicate\n")
        with self.assertRaisesRegex(validator.ValidationError, "duplicate.*L-001"):
            validator.validate_project(root, changed_files=[])

    def test_activity_history_must_be_append_only(self) -> None:
        old = "# Activity\n\n## A-001 — 2026-07-15T20:00:00Z — Old\n"
        new = "# Activity\n\n## A-001 — 2026-07-15T20:00:00Z — Rewritten\n"
        with self.assertRaisesRegex(validator.ValidationError, "append-only"):
            validator.ensure_append_only(old, new)
        validator.ensure_append_only(old, old + "\n## A-002 — 2026-07-15T21:00:00Z — New\n")

    def test_material_change_requires_status_and_activity(self) -> None:
        changed = {
            "circuits/spa-francorchamps/seasons/2026/plans/example.md",
        }
        with self.assertRaisesRegex(validator.ValidationError, "STATUS.md"):
            validator.validate_required_record_updates(changed)

    def test_spec_change_requires_decision_record(self) -> None:
        changed = {
            "circuits/spa-francorchamps/seasons/2026/specs/example.md",
            "circuits/spa-francorchamps/seasons/2026/project/STATUS.md",
            "circuits/spa-francorchamps/seasons/2026/project/ACTIVITY.md",
        }
        with self.assertRaisesRegex(validator.ValidationError, "DECISIONS.md"):
            validator.validate_required_record_updates(changed)

    def test_review_change_requires_lesson_or_explicit_no_new_lesson(self) -> None:
        changed = {
            "circuits/spa-francorchamps/seasons/2026/reviews/example.md",
            "circuits/spa-francorchamps/seasons/2026/project/STATUS.md",
            "circuits/spa-francorchamps/seasons/2026/project/ACTIVITY.md",
        }
        with self.assertRaisesRegex(validator.ValidationError, "LESSONS.md"):
            validator.validate_required_record_updates(changed, activity_text="lessons reviewed later")
        validator.validate_required_record_updates(
            changed,
            activity_text="**Lessons review:** no-new-lesson.",
        )
        validator.validate_required_record_updates(
            changed,
            activity_text="lessons_reviewed: no-new-lesson",
        )


if __name__ == "__main__":
    unittest.main()
