---
schema: race-lab-project-maintenance/v1
initiative: spa-2026-calibration
authority: normative
---

# Spa 2026 Project-Control Records

This directory is the durable control surface for the Spa 2026 Race Lab initiative. Conversation memory, project summaries, PR comments, and agent reports are useful evidence, but none replaces these records plus direct inspection of repository and pull-request state.

## Record authority

- `STATUS.md` is the authoritative replace-in-place snapshot of current objective, active tasks, blockers, evidence, publication state, review-action counts, and next exact action.
- `ACTIVITY.md` is append-only history. It records attempts, partial loops, failures, verification, commits, pushes, and remote actions. Existing entries are never rewritten; corrections are appended.
- `DECISIONS.md` records load-bearing decisions, rationale, rejected alternatives, affected interfaces, and reversal conditions.
- `LESSONS.md` records frictions and mistakes, systemic causes, consequences, enforceable guardrails, and evidence that the guardrails work.
- `../plans/2026-07-15-pr1-closeout-plan.md` is the active closeout plan. Stable task IDs are the interface between the plan and `STATUS.md`. Closeout task IDs may use one uppercase suffix (for example `PR-03C`) when a parent gate is split without renumbering historical tasks.

## Start-of-session procedure

Before substantive work:

1. Read this file.
2. Read `STATUS.md`.
3. Read the latest relevant entries in `ACTIVITY.md`, `DECISIONS.md`, and `LESSONS.md`.
4. Inspect the actual branch, PR head, review threads, commits, and verification/CI state when tools permit.
5. Compare recorded and actual state.
6. Append a correction activity entry and update `STATUS.md` before relying on stale or contradictory records.
7. State the current objective and next exact action.

## During-work rules

- Prefer one internally coherent, verified publication unit over partial pushes.
- Do not reopen approved architecture during bounded closeout unless a finding exposes a genuine contradiction.
- Keep planning, implementation, validation, release, and historical record distinct.
- When an interface or schema changes, search specifications, plans, reviews, implementation, tests, generators, validators, browser integration, and documentation for every producer and consumer.
- Track review actions separately: finding evaluated, artifact changed, reaction applied, inline reply posted, thread resolved, and fresh review requested.
- Executable code or control changes require an executable workspace; connector-only replacement is not integration evidence.
- Before declaring a workspace present or lost, verify its exact path, `.git`, branch/HEAD, status, and expected file inventory.
- Treat remote worker full-file rewrites as untrusted until complete content, byte/line counts, and diff statistics are compared with the exact base.
- Temporary branches require an explicit cleanup gate; retain only the active PR branch and a deliberately named evidence archive when necessary.
- If interrupted, record the exact partial count. Never leave a procedural sweep implicit.

## End-of-session procedure

Before completion, publication, or handoff:

1. Update `STATUS.md`.
2. Append `ACTIVITY.md`.
3. Update `DECISIONS.md` when a load-bearing decision changed.
4. Update `LESSONS.md` when a new friction, failure, or reusable guardrail emerged; otherwise record `lessons_reviewed: no-new-lesson` in the activity entry.
5. Run `bash scripts/verify.sh` and read the complete output.
6. Record exact evidence and remaining incompleteness.
7. Distinguish local, committed, pushed, remotely observed, reviewed, and CI-confirmed states.
8. Leave one precise next action.

## Evidence vocabulary

Use only these labels for important state claims:

- `locally-verified`: directly checked in the current local environment.
- `committed`: present in a named local or repository commit.
- `pushed`: a branch ref was updated to include the commit.
- `remotely-observed`: read back from GitHub or another external system.
- `reviewed`: assessed by a named reviewer against a named head.
- `CI-confirmed`: supported by a retrievable workflow/check result.
- `reported-but-unverified`: stated in a prior message or comment without retrievable direct evidence.

A claim may carry more than one label. Never infer one label from another.

## Mutation rules

### `STATUS.md`

Replace in place. Its front matter must remain machine-readable. Active task IDs must exist in the active plan and must not be marked complete there. Review counters must be internally consistent.

The status file records the last directly observed remote head. It does not attempt to contain the SHA of the commit that contains itself. The current record commit is obtained from Git.

### `ACTIVITY.md`

Append only. Each entry uses a unique `A-NNN` ID and an ISO-8601 timestamp. A correction references the entry it corrects. Existing text is historical evidence and is not silently rewritten.

### `DECISIONS.md`

Use unique `D-NNN` IDs. Superseded or reversed decisions remain in place with status and links to the successor decision.

### `LESSONS.md`

Use unique `L-NNN` IDs. A lesson is not complete until it names an enforceable guardrail and how that guardrail is checked.

## Freshness and recovery

Repository-dependent facts must include an observation time and evidence source. At the start of a new session, inspect actual state before trusting them.

When records disagree:

1. Do not select the most convenient account.
2. Inspect Git, the PR, reviews, and verification evidence.
3. Append a correction activity entry describing the discrepancy and source of truth.
4. Update `STATUS.md`.
5. Update `DECISIONS.md` only if the governing decision changed.
6. Add or revise a lesson when the discrepancy exposes a reusable systemic weakness.

## Automated enforcement

`scripts/verify_project_control.py` checks:

- required files and front matter;
- stable and unique task/activity/decision/lesson IDs;
- active-task references and completion state;
- review-counter consistency;
- required activity-entry sections and monotonic timestamps;
- append-only activity history when a merge base contains prior entries;
- diff-coupled record updates;
- review reconciliations record lesson review in the newest appended activity entry rather than reusing a historical marker;
- placeholder and malformed-record failures.

`scripts/verify.sh` invokes this validator. `.github/workflows/verify.yml` invokes the canonical verifier on pull requests and pushes. Branch protection should require that workflow before merge when repository settings permit.
