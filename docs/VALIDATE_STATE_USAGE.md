# Hermes `validate-state` Usage

This document describes how operators run the Hermes `validate-state` command
introduced in v0.3-E and how to interpret its output. It also points to example
`state.json` records under [`examples/state/`](examples/state/) that show
common valid and invalid shapes.

`validate-state` is read-only. It does not create, modify, or transition any
state. It does not approve, run, push, merge, or deploy anything. It does not
parse `reviewer_report.md`, `queue.md`, `log.md`, or dry-run evidence. It does
not block or change `run-next` or `plan-status`. State machine, reviewer gate,
and queue/dry-run evidence enforcement are not connected to runtime in v0.3-F.

## Commands

```bash
python3 hermes.py validate-state <plan_id>
python3 hermes.py validate-state <plan_id> --state-file <path>
```

Default input path:

```
.hermes/plans/<plan_id>/state.json
```

`--state-file` overrides the input path so operators can validate sample
records or fixtures without touching real plan state under `.hermes/`.

The `plan_id` argument must match the `plan_id` field inside the record.
A mismatch fails validation with reason `plan_id_mismatch`.

## Output Shape

Successful run:

```
state_validation: pass
plan_id: <plan_id>
state_file: <absolute path>
errors: 0
warnings: 0
note: validator is read-only and does not approve, transition, or modify state
```

Failed run:

```
state_validation: fail
plan_id: <plan_id>
state_file: <absolute path>
errors: <N>
warnings: <N>
error: field=<name> reason=<reason> ...
note: validator is read-only and does not approve, transition, or modify state
```

Warnings are reported but do not by themselves cause failure. `errors > 0` is
the only failure condition for exit code `1`.

## Exit Codes

| code | meaning |
| --- | --- |
| `0` | validation passed (zero errors; warnings allowed) |
| `1` | validation failed (one or more rule violations) |
| `2` | usage error, missing file, unreadable file, or invalid JSON |

Exit `2` is reserved for problems before validation can run. Examples: state
file does not exist, the path points to a directory, the file is not valid
JSON, the JSON root is not an object, or the CLI argument is malformed.

## Review Gate Behavior

`review_gate_snapshot` is an optional field. When present, the validator
applies these rules:

- `open`: validator does **not** treat this as automatic approval. The plan
  must still go through the manual reviewer process documented in
  [OPERATOR_CHECKLIST.md](OPERATOR_CHECKLIST.md). No execution gate is
  enforced from this field alone.
- `unknown`: validator emits a warning with reason `operator_review_required`
  and still passes (exit code `0` if no other errors). The operator must
  resolve the reviewer state manually before the plan proceeds.
- `blocked_by_reviewer`: combining this with `state: approved_for_manual_run`
  or `state: running` fails with reason `reviewer_blocked`. Reviewer block
  must be cleared by re-entering `awaiting_review` first.
- Any other string fails with reason `unknown_review_gate`.

## Forbidden Transitions

Transitions to `running` are forbidden from every state except
`approved_for_manual_run`. In particular the validator rejects:

- `archived -> running`
- `blocked_by_reviewer -> running`
- `completed -> running`
- `failed -> running`
- `cancelled -> running`
- `draft -> running`
- `queued -> running`
- `dry_run_ready -> running`
- `awaiting_review -> running`

These appear in output with reason `forbidden_transition` and a value such as
`blocked_by_reviewer->running`.

Other unsupported transitions (for example `queued -> completed`) fail with
reason `invalid_transition`.

## What `validate-state` Does Not Do

`validate-state` deliberately stays small. It does **not**:

- generate or scaffold `state.json` records
- write to `state.json` or any other plan file
- transition a plan from one state to another
- append history entries
- parse `reviewer_report.md`, `queue.md`, `log.md`, or dry-run evidence
- block, gate, or change the behavior of `run-next`
- block, gate, or change the behavior of `plan-status`
- execute Codex or any unit
- push, merge, deploy, or auto-approve anything
- track `.hermes/` under Git

Runtime enforcement of the state machine and reviewer gate is intentionally
deferred to a later milestone.

## Examples

Sample records live under [`examples/state/`](examples/state/):

| file | shape | expected outcome |
| --- | --- | --- |
| `valid_draft_state.json` | initial `draft` record, empty history | pass |
| `valid_awaiting_review_state.json` | full lifecycle up to `awaiting_review` with `review_gate_snapshot: open` | pass |
| `invalid_unknown_state.json` | `state: made_up_state` | fail (`unknown_state`) |
| `invalid_blocked_running_state.json` | `blocked_by_reviewer -> running` with `review_gate_snapshot: blocked_by_reviewer` | fail (`forbidden_transition` and `reviewer_blocked`) |

Run them with:

```bash
python3 hermes.py validate-state example-plan \
  --state-file docs/examples/state/valid_draft_state.json

python3 hermes.py validate-state example-plan \
  --state-file docs/examples/state/valid_awaiting_review_state.json

python3 hermes.py validate-state example-plan \
  --state-file docs/examples/state/invalid_unknown_state.json

python3 hermes.py validate-state example-plan \
  --state-file docs/examples/state/invalid_blocked_running_state.json
```

The first two should exit `0` with `state_validation: pass`. The last two
should exit `1` with `state_validation: fail` and at least one `error:` line
naming the failing field and reason.

## Related Documents

- [PLAN_STATE_MACHINE.md](PLAN_STATE_MACHINE.md) — lifecycle states and allowed
  transitions.
- [PLAN_STATE_RECORD_SCHEMA.md](PLAN_STATE_RECORD_SCHEMA.md) — record shape and
  required fields.
- [STATE_RECORD_VALIDATION_RULES.md](STATE_RECORD_VALIDATION_RULES.md) — full
  validation contract.
- [MINIMAL_STATE_VALIDATOR_PLAN.md](MINIMAL_STATE_VALIDATOR_PLAN.md) — scope of
  the v0.3-E validator implementation.
- [OPERATOR_CHECKLIST.md](OPERATOR_CHECKLIST.md) — manual review process.
