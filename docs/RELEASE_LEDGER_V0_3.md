# Hermes v0.3 Release Ledger

This ledger records the completed Hermes v0.3-A through v0.3-I release line.

It is a closure document, not an execution plan. It does not introduce new
runner behavior, automation, reviewer execution, state transition enforcement,
push, merge, or deploy capability.

## Purpose

This document gives operators a human-auditable release ledger for the full
v0.3 line and collects the safety boundaries confirmed by that work.

It should be used to answer two questions:

- what changed in each v0.3 round
- which safety boundaries remain active after v0.3

## Round Summary

- v0.3-A: plan state machine docs
- v0.3-B: plan state record schema docs
- v0.3-C: state record validation rules docs
- v0.3-D: minimal state validator implementation plan
- v0.3-E: minimal read-only `validate-state` CLI
- v0.3-F: `validate-state` usage docs/examples
- v0.3-G: `validate-state` integration boundary docs
- v0.3-H: `plan-status` read-only state validation summary
- v0.3-I: `plan-status` state validation interpretation guide

## v0.3 Release Ledger

| round | intent | artifact / touched docs | behavior impact | safety boundary |
| --- | --- | --- | --- | --- |
| v0.3-A | Define plan state machine docs. | `docs/PLAN_STATE_MACHINE.md` | Documentation only. Defines lifecycle states and allowed transitions. | No runtime state machine enforcement. No automatic state transition. |
| v0.3-B | Define plan state record schema docs. | `docs/PLAN_STATE_RECORD_SCHEMA.md` | Documentation only. Defines the intended `state.json` record shape. | No `state.json` generation, repair, update, or Git tracking change. |
| v0.3-C | Define state record validation rules docs. | `docs/STATE_RECORD_VALIDATION_RULES.md` | Documentation only. Defines validation rules before implementation. | No validator execution path and no enforcement. |
| v0.3-D | Plan minimal state validator implementation. | `docs/MINIMAL_STATE_VALIDATOR_PLAN.md` | Documentation only. Defines a narrow read-only validator scope. | No code behavior change. No `run-next`, reviewer gate, or state machine enforcement. |
| v0.3-E | Add minimal read-only `validate-state` CLI. | `hermes.py`, `scripts/smoke_v0_3_e_validate_state.sh`, `docs/examples/state/*` | Adds a manual validator for one selected `state.json` record. | Validator is read-only. It does not create, modify, transition, approve, run, push, merge, or deploy. |
| v0.3-F | Document `validate-state` usage and examples. | `docs/VALIDATE_STATE_USAGE.md`, `README.md` | Documentation only. Explains command usage, exit codes, and sample state records. | Validation remains manual and read-only. It does not block `run-next` or change `plan-status`. |
| v0.3-G | Define `validate-state` integration boundary docs. | `docs/VALIDATE_STATE_INTEGRATION_BOUNDARY.md` | Documentation only. Defines integration levels and the current Level 1 target. | No `run-next` integration, reviewer gate enforcement, state mutation, or hidden automation. |
| v0.3-H | Show read-only state validation summary in `plan-status`. | `hermes.py`, `scripts/smoke_v0_3_h_plan_status_state_validation.sh`, `README.md` | `plan-status` displays a Level 1 informational validation summary when possible. | Summary is not enforcement. Exit code behavior, `run-next`, reviewer gates, and state transitions remain unchanged. |
| v0.3-I | Add `plan-status` state validation interpretation guide. | `docs/PLAN_STATUS_STATE_VALIDATION_GUIDE.md`, `README.md` | Documentation only. Explains how operators read `pass`, `fail`, `error`, and `not_found`. | Results are human review signals only. They do not approve execution or automatically block execution. |

## Final v0.3 Safety Boundary

The v0.3 line closes with these boundaries still active:

- `validate-state` is a read-only validator.
- `plan-status` state validation is a Level 1 informational display.
- State validation is not an execution approval or blocking signal.
- `review_gate: open` is not execution approval.
- Manual Review Checkpoints are a human-authored audit log.
- `run-next` enforcement is not implemented.
- `state.json` is not automatically created, modified, repaired, or
  transitioned.
- Reviewer gate enforcement is not implemented.
- State machine enforcement is not implemented.
- Auto reviewer execution is not implemented.
- Auto push, merge, and deploy are not implemented.
- `.hermes/` remains local ignored runtime state.
- No enforcement is active in v0.3.

## Operator Interpretation

`state_validation: pass`, `state_validation: fail`,
`state_validation: error`, and `state_validation: not_found` are information
for a human operator to inspect.

Do not interpret these values as automatic permission to execute work. Do not
interpret them as automatic denial of work. They are read-only validation
signals that must be evaluated alongside the queue, reviewer report, manual
checkpoints, and any other release evidence.

`review_gate: open` has the same boundary: it is a reviewer status summary, not
an execution approval.

## Closure Statement

Hermes v0.3 built read-only validation visibility and documented the boundary
around plan state records, validation, reviewer gates, and operator
interpretation.

Hermes v0.3 did not introduce enforcement, automatic state transitions,
automatic reviewer execution, automatic queue execution, run-all behavior, model
routing, auto push, auto merge, or auto deploy.
