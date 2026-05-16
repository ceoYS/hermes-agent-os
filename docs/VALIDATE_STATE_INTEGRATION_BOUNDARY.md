# Hermes `validate-state` Integration Boundary

This document defines the safety boundary for any future integration between
`validate-state` and the rest of Hermes.

v0.3-G is documentation only. It does not connect `validate-state` to
`plan-status`, `run-next`, reviewer gates, operator checklists, state
transitions, or any automatic enforcement path.

## Purpose

`validate-state` now gives operators a read-only way to inspect a single
`state.json` record. Before wiring that signal into other Hermes commands, the
integration boundary must be explicit.

The purpose of v0.3-G is to decide what must stay safe while future integration
points are evaluated:

- validation must remain read-only
- validation output must be visible to the operator before it can become
  enforcement
- state validation must not silently become execution approval
- reviewer signals and state validation must stay distinct unless a later
  milestone deliberately defines a combined policy

Current v0.3-G behavior: documentation only. No implementation is added.

## Possible Future Integration Points

### Manual Operator Command

The current command remains the only implemented integration level:

```bash
python3 hermes.py validate-state <plan_id>
```

Operators may also use `--state-file <path>` for fixtures or explicit input, as
documented in [VALIDATE_STATE_USAGE.md](VALIDATE_STATE_USAGE.md).

### `plan-status` Informational Display

A future `plan-status` integration could read `.hermes/plans/<plan_id>/state.json`
when that file exists and display a validation summary, for example:

```text
state_validation: pass
state_validation_errors: 0
state_validation_warnings: 1
```

If no state file exists, `plan-status` could show:

```text
state_validation: not_found
```

This candidate is informational only. It must not change `plan-status` exit
codes, queue parsing behavior, reviewer gate display, or `run-next` behavior.

### `run-next` Preflight Check

A future `run-next` integration could run validation as a preflight check before
reporting or selecting the next runnable queue unit.

This is a future candidate only. The default block policy is not decided. A
warning-only mode should be considered before any blocking mode.

### Reviewer Gate Relationship

`validate-state` does not replace `reviewer_report.md`.

The `review_gate` summary and state validation are separate signals:

- reviewer gate data comes from reviewer verdict workflow
- state validation checks the shape and lifecycle consistency of a state record
- `review_gate: open` is not execution approval
- `review_gate: blocked_by_reviewer` is not automatically resolved by a passing
  state validation result
- unknown reviewer state still requires operator review

A future policy may decide how these signals interact, but v0.3-G does not
combine them.

### Operator Checklist

A future operator checklist flow could recommend a manual validation step before
merge, run, or release operations:

```bash
python3 hermes.py validate-state <plan_id>
```

That flow should remain human-operated unless a later milestone explicitly
defines warning, override, and enforcement behavior.

## Integration Levels

| level | name | behavior |
| --- | --- | --- |
| Level 0 | Manual only | Operator runs `validate-state` directly and interprets output. |
| Level 1 | `plan-status` informational display only | `plan-status` displays read-only validation summary when possible. |
| Level 2 | `run-next` warning only | `run-next` reports validation warnings or failures but does not block. |
| Level 3 | `run-next` soft block with explicit override | `run-next` blocks by default only under a documented override policy. |
| Level 4 | Hard enforcement | Hermes refuses unsafe transitions or execution without override. |

Current implementation is close to Level 0. `validate-state` exists as a manual,
read-only command, but Hermes does not automatically invoke it from other
commands.

v0.3-G does not implement Levels 1 through 4.

## Recommended Next Step

The recommended next implementation candidate is Level 1:

- update `plan-status` to display a read-only validation summary when
  `.hermes/plans/<plan_id>/state.json` exists
- display `state_validation: not_found` or an equivalent summary when the file
  does not exist
- keep `plan-status` exit code behavior unchanged
- keep `run-next` behavior unchanged
- avoid creating or modifying `state.json`
- avoid treating validation output as execution approval

Level 1 is preferred because it makes validation operator-visible before Hermes
starts using validation as a warning or block signal.

## What Must Not Happen Yet

Future work must not introduce these behaviors until a later milestone
explicitly defines and reviews them:

- `validate-state` failure must not automatically block `run-next`
- `validate-state` failure must not automatically block PR, merge, tag, or
  release operations
- `state.json` must not be generated automatically
- a passing state validation result must not be interpreted as reviewer approval
- `review_gate: open` must not be interpreted as execution approval
- `review_gate: blocked_by_reviewer` must not be bypassed by state validation
- `review_gate: unknown` must not be silently treated as safe
- validation must not mutate state, append history, or transition lifecycle
  state
- `.hermes/` must not become Git-tracked runtime state

## Safety Principles

Future integration should follow these principles:

- read-only first
- operator-visible before enforcement
- warning before blocking
- explicit override policy before any soft or hard block
- no hidden automation
- no state mutation during validation
- reviewer evidence remains distinct from state record validation
- dry-run evidence does not imply execution approval

## Future Decision Points

Later milestones need explicit decisions before moving beyond Level 0:

- whether `plan-status` should display validation summary
- whether `run-next` should show validation warnings only
- when `blocked_by_reviewer` should become a hard block
- whether unknown `review_gate` should remain a warning or become a block
- how override decisions should be recorded in `.hermes/plans/<plan_id>/log.md`
- whether validation summary needs machine-readable output before integration
- which command owns any future override flag and audit text

Until those decisions are made, `validate-state` remains a manual read-only
operator command.
