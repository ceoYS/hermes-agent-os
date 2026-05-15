# Minimal Hermes State Validator Plan

This document defines the implementation plan for a minimal read-only Hermes
plan state validator in v0.3-E.

v0.3-D is documentation only. It does not implement a validator, create
`state.json`, enforce the state machine, enforce reviewer gates, change
`run-next`, change `plan-status`, add a runner, or add automation.

## Purpose

The v0.3-E validator should provide the smallest useful read-only check for a
single explicit plan state record before any lifecycle enforcement is added.

This plan fixes the intended command shape, input scope, output format, exit
codes, minimal validation scope, and smoke coverage before implementation.

Current v0.3-D behavior: no validator code exists.

## Proposed Command

Primary candidate:

```bash
python3 hermes.py validate-state <plan_id>
```

Safer candidate with explicit input:

```bash
python3 hermes.py validate-state <plan_id> --state-file <path>
```

v0.3-E should validate only. It should not transition state, execute work,
modify files, generate files, repair records, append history, or approve any
plan action.

## Input Scope

Future default candidate:

```text
.hermes/plans/<plan_id>/state.json
```

Optional direct input candidate:

```bash
--state-file <path>
```

The validator should read the selected input file only. It should not write to
the file, create a missing file, update `.hermes/`, or change Git state.

`.hermes/` remains local runtime ignored state. This plan does not make
`.hermes/` a Git-tracked directory.

## Output Format

The default output should be human-readable and stable enough for smoke tests.

Candidate summary lines:

```text
state_validation: pass
errors: 0
warnings: 0
```

```text
state_validation: fail
errors: 2
warnings: 1
```

Error details should include:

- field or JSON path
- reason
- expected value or shape when useful
- observed value when safe to display

Candidate detail shape:

```text
error: field=state reason=unknown_state value=paused
error: field=previous_state/state reason=invalid_transition value=queued->running
warning: field=review_gate_snapshot.review_gate reason=operator_review_required value=unknown
```

JSON output may be considered later, for example with a future `--json` flag.
It is not required for v0.3-E.

## Exit Code Plan

| exit code | meaning |
| --- | --- |
| `0` | Validation passed. |
| `1` | Validation failed. |
| `2` | Usage error, missing file, or unreadable file. |

The validator should not automatically fix records for any exit code.

## Minimal Validation Scope For v0.3-E

v0.3-E should implement only these read-only checks:

- required top-level fields exist
- `state` uses a known lifecycle state value
- `previous_state` is null for an initial `draft` record or uses a known state
- `previous_state` -> `state` follows the allowed direct transition graph
- `updated_at` has a basic ISO-8601 timestamp shape
- `history` is a list
- `review_gate_snapshot.review_gate` has a known basic value when present
  (`open`, `blocked_by_reviewer`, or `unknown`)
- `archived` cannot transition to `running`
- `blocked_by_reviewer` cannot transition to `running`

History rewrite detection is not required yet unless it is trivially checkable
from the current record alone.

## Explicitly Out Of Scope For v0.3-E

v0.3-E should not add:

- automatic state transition
- `state.json` generation
- writes to `state.json`
- history append behavior
- reviewer gate enforcement
- reviewer report parsing changes
- `plan-status` behavior changes
- `run-next` behavior changes
- automatic execution
- `run-all`
- model routing
- automatic push, merge, or deploy
- automatic reviewer execution
- state machine enforcement during `run-next`
- global execution blocking
- Git tracking changes for `.hermes/`

## Proposed Validation Cases And Smoke Plan

Future smoke coverage should use small temporary state record fixtures and
should not write to real `.hermes/` runtime state.

| case | expected result | expected exit |
| --- | --- | --- |
| Valid minimal `draft` state | pass | `0` |
| Missing required field | fail | `1` |
| Unknown `state` value | fail | `1` |
| Invalid transition | fail | `1` |
| `blocked_by_reviewer` -> `running` | fail | `1` |
| `archived` -> `running` | fail | `1` |
| Malformed `updated_at` | fail or warn by documented policy | `1` or `0` |
| `history` is not a list | fail | `1` |
| Unknown `review_gate` | warn or require operator review by documented policy | `0` or `1` |
| Unreadable state file | usage/input error | `2` |
| Missing state file | usage/input error | `2` |

The v0.3-E implementation should choose and document the exact `updated_at` and
unknown `review_gate` behavior before adding smoke assertions.

## Safety Principles

The v0.3-E validator should be:

- read-only
- deterministic
- local-only
- network-free
- independent of Codex invocation
- free of Git writes
- free of `.hermes/` tracking changes
- free of automatic repair
- free of automatic approval

It should validate only the state record explicitly selected by the operator.

## v0.3-E Implementation Boundary

v0.3-E should implement only the minimal read-only validator described here. It
should include smoke coverage for the selected command, input, output, and exit
code behavior.

It should not enforce the plan lifecycle during `run-next`, block execution
globally, generate state records, mutate plan files, or treat reviewer status as
automatic approval.

The implementation target is a narrow validation command for an explicitly
provided state record.
