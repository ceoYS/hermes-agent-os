# Hermes Agent OS

Hermes v0 is a local single-task runner for safe Codex execution.

## v0 Goal

Read one task.yaml, validate it, create an isolated Git worktree, build prompt.md, optionally run codex exec, capture logs, save git outputs, append journal.jsonl, and write state.json.

## v0.1 Local Smoke Tests

Prefer the portable smoke script. It creates a temporary Git repository, task file, and runs root under `/tmp`, then runs the v0.1 non-nested smoke checks.

```bash
bash scripts/smoke_v0_1.sh
```

The script uses `python3 hermes.py run ... --no-codex`; it does not launch nested Codex.

`examples/trader-review.yaml` remains a machine-specific sample. If that repository path does not exist on the current machine, use the smoke script above or adjust a local-only copy before running manual validate/dry-run/run commands.

## v0.2-A Plan Scaffold

Hermes can create and inspect local Crack-lite plan scaffold directories without running Codex or executing queue units.

```bash
python3 hermes.py plan-init trader-d129-docs-only --title "Trader D129 docs-only review" --objective "Prepare a docs-only review plan"
python3 hermes.py plan-status trader-d129-docs-only
```

Generated `.hermes/` runtime plans are local artifacts and are ignored by Git. Do not commit generated `.hermes/plans/*` directories.

## v0.2-B Queue Parser

`plan-status` now parses `.hermes/plans/<plan_id>/queue.md` and reports queue counts, units, and parser warnings without modifying plan state or executing any queue units.

Supported queue statuses:
- pending
- running
- completed
- needs_work
- failed
- skipped

Smoke test:

```bash
bash scripts/smoke_v0_2_b_queue_parser.sh
```

## v0.2-C Run Next Dry Run

Hermes can inspect a plan queue and report the first runnable pending unit without executing Codex or modifying plan files.

```bash
python3 hermes.py run-next trader-d129-docs-only --dry-run
```

`--dry-run` is required. Real queue unit execution is not implemented in v0.2-C.

Selection rules:
- candidate units must have status `pending`
- dependencies may be `-`, empty, or comma-separated unit ids
- a pending unit is runnable only when every dependency exists and has status `completed`
- blocked pending units report `dependency_not_completed:<unit_id>` or `dependency_missing:<unit_id>`

Smoke test:

```bash
bash scripts/smoke_v0_2_c_run_next_dry_run.sh
```

## v0.2-D Reviewer Report

`plan-init` now creates a plan-level `.hermes/plans/<plan_id>/reviewer_report.md`.
There is one reviewer report per plan for now, not per queue unit.

`plan-status` reports whether the reviewer report exists and reads a simple `verdict:` field.
Accepted verdicts are `pending`, `pass`, `pass_with_notes`, `needs_work`, and `blocked`.
`needs_work` and `blocked` are reviewer stop signals: the plan should not proceed until reviewed and fixed.

Smoke test:

```bash
bash scripts/smoke_v0_2_d_reviewer_report.sh
```
