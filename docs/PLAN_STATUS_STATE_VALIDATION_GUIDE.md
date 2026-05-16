# Hermes `plan-status` State Validation Guide

This guide explains how operators should read the `state_validation` summary
shown by:

```bash
python3 hermes.py plan-status <plan_id>
```

The summary is a Level 1 informational display. It is not enforcement. It does
not approve execution, change reviewer gates, transition state, create files,
or change `run-next` behavior.

## Quick Rules

- `plan-status` reads `.hermes/plans/<plan_id>/state.json` when it exists.
- `plan-status` must not create or repair `state.json`.
- `plan-status` keeps exit code `0` when it can show the plan summary, even
  when the validation summary is `fail` or `error`.
- `validate-state` failures do not automatically block `run-next`.
- `review_gate: open` is not execution approval.
- Manual Review Checkpoints remain a human-authored audit log.
- The state validation summary does not replace human review.

## `state_validation: not_found`

What it means:

`state.json` does not exist at `.hermes/plans/<plan_id>/state.json`. This is not
an error. Some plans may not have a state record yet.

What to do:

If the operator needs validation, prepare a `state.json` record manually and run
`plan-status` again or run `validate-state` directly.

What not to do:

Do not treat `not_found` as a failure signal. Do not generate `state.json`
automatically.

## `state_validation: pass`

What it means:

The current `state.json` passed the minimal validator checks. The summary may
also show warning counts when warnings are present.

What to do:

Use this as one read-only signal while inspecting the plan, queue, reviewer
report, and manual checkpoints.

What not to do:

Do not treat `pass` as execution approval. Do not treat it as a human reviewer
decision. It is separate from `review_gate`, and `review_gate: open` is also
not execution approval.

## `state_validation: fail`

What it means:

`state.json` was read and parsed, but one or more validation rules failed.
`plan-status` reports the summary only; it still exits `0` when the rest of the
plan summary can be shown.

What to do:

Inspect `state.json` and run `python3 hermes.py validate-state <plan_id>` if
the full validator output is needed.

What not to do:

Do not treat `fail` as an automatic `run-next` stop condition. Hermes does not
enforce the state machine or reviewer gate from the `plan-status` summary.

## `state_validation: error`

What it means:

`state.json` exists, but Hermes could not read it as a valid state record. Common
causes include invalid JSON, a path problem, unreadable content, or a JSON root
that is not an object.

What to do:

Check the file path, file permissions, and JSON syntax. Then rerun
`plan-status` or `validate-state`.

What not to do:

Do not automatically repair, overwrite, or regenerate the file.

## Review Boundary

State validation and human review are separate signals:

- `state_validation` describes the shape and lifecycle consistency of
  `state.json`.
- `review_gate` describes the current reviewer verdict summary.
- `Manual Review Checkpoints` record human-authored audit history.

The operator must continue to inspect reviewer evidence and checkpoint history.
The `plan-status` state validation summary is a read-only aid, not a replacement
for human review.
