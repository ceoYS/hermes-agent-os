# Hermes Agent OS

Hermes v0 is a local single-task runner for safe Codex execution.

Release ledger: see [RELEASES.md](RELEASES.md) for the v0.2-A through v0.2-G
closure state, tag mapping, and safety boundaries.

Operator closure docs: see [docs/OPERATOR_CHECKLIST.md](docs/OPERATOR_CHECKLIST.md)
and [docs/V0_3_ENTRY_CRITERIA.md](docs/V0_3_ENTRY_CRITERIA.md).

Plan state machine design: see [docs/PLAN_STATE_MACHINE.md](docs/PLAN_STATE_MACHINE.md).
Plan state record schema design: see [docs/PLAN_STATE_RECORD_SCHEMA.md](docs/PLAN_STATE_RECORD_SCHEMA.md).

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

## v0.2-E Reviewer Gate

`plan-status` summarizes the plan-level reviewer verdict as `review_gate`.
The reviewer verdict is recorded in `.hermes/plans/<plan_id>/reviewer_report.md`.

Gate mapping:
- `review_gate: blocked_by_reviewer` comes from `verdict: needs_work` or `verdict: blocked`
- `review_gate: open` comes from `verdict: pending`, `verdict: pass`, or `verdict: pass_with_notes`
- `review_gate: unknown` comes from a missing verdict or an unknown verdict value

Hermes does not make an automatic merge, execution, or reviewer decision from this gate.
It is a status summary for the human operator to inspect before deciding what to do next.

Smoke test:

```bash
bash scripts/smoke_v0_2_e_review_gate.sh
```

## v0.2-F Manual Review Checkpoints

`plan-init` also creates a plan-level `.hermes/plans/<plan_id>/log.md` with a
`Manual Review Checkpoints` section.

Use this section as a human-maintained audit log for major review decisions:
- who reviewed the plan
- which checkpoint was reviewed
- what verdict was recorded
- any notes or links needed for later audit

The checkpoint table is not an automatic source of truth for Hermes decisions.
`reviewer_report.md` remains the machine-readable place for the current reviewer verdict,
and `plan-status` remains the command that displays the derived `review_gate`.

Smoke test:

```bash
bash scripts/smoke_v0_2_f_review_checkpoint_log.sh
```

## v0.2-G Review Workflow

A typical manual reviewer workflow is:

```bash
python3 hermes.py plan-init trader-d129-docs-only --title "Trader D129 docs-only review" --objective "Prepare a docs-only review plan"
```

Edit `.hermes/plans/trader-d129-docs-only/queue.md` so the planned units are explicit.
Then inspect the next runnable unit without executing it:

```bash
python3 hermes.py run-next trader-d129-docs-only --dry-run
```

After a human or external reviewer checks the plan, record the current verdict in
`.hermes/plans/trader-d129-docs-only/reviewer_report.md`:

```markdown
verdict: pass_with_notes
```

Check the gate summary:

```bash
python3 hermes.py plan-status trader-d129-docs-only
```

If `plan-status` shows `review_gate: blocked_by_reviewer`, the plan should not proceed
until the `needs_work` or `blocked` verdict is resolved. If it shows `review_gate: open`,
the reviewer verdict is non-blocking. If it shows `review_gate: unknown`, inspect
`reviewer_report.md` for a missing or unsupported verdict.

Finally, append a human-readable checkpoint row to
`.hermes/plans/trader-d129-docs-only/log.md` under `Manual Review Checkpoints`.
That checkpoint is for audit history only; it does not replace the current verdict in
`reviewer_report.md`.

Hermes v0.2 still has no automatic queue execution, automatic merge, automatic reviewer,
model routing, or run-all behavior.
