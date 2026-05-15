# Hermes State Record Validation Rules

This document defines the future validation contract for the Hermes plan state
record described in [PLAN_STATE_RECORD_SCHEMA.md](PLAN_STATE_RECORD_SCHEMA.md)
and the lifecycle described in [PLAN_STATE_MACHINE.md](PLAN_STATE_MACHINE.md).

v0.3-C is documentation only. It does not implement a `state.json` validator,
state generation, state machine enforcement, reviewer gate enforcement,
`run-next` behavior changes, or `plan-status` behavior changes.

## Purpose

This document fixes the PASS/FAIL contract for a future state record validator
before any validator or state transition checker is implemented.

The future validator should use these rules to decide whether a proposed
`.hermes/plans/<plan_id>/state.json` record is structurally valid, uses a known
state, follows an allowed transition, preserves audit history, and carries the
required evidence for review-sensitive lifecycle changes.

Current v0.3-C behavior: no validation code exists.

## Validation Categories

Future validation should be grouped into these categories:

| category | purpose |
| --- | --- |
| Schema validation | Confirm required fields, field types, nullable fields, and timestamp shape. |
| State value validation | Confirm `state` and related state fields use known lifecycle states. |
| Transition validation | Confirm direct state changes follow the allowed transition graph. |
| Reviewer gate validation | Confirm reviewer stop signals are not treated as approval. |
| Manual checkpoint reference validation | Confirm manual approvals and override-like decisions have human audit evidence. |
| Queue/dry-run evidence validation | Confirm queue and dry-run evidence exists before validation-derived promotions. |
| History validation | Confirm transition history is append-only and each entry has required evidence. |
| Archive/finality validation | Confirm terminal and archived records do not silently become active again. |

These are proposed validation categories only. v0.3-C does not add smoke
scripts, CLI commands, or runtime checks for them.

## Schema Validation Rules

Future validation should require these top-level fields:

- `schema_version`
- `plan_id`
- `state`
- `updated_at`
- `updated_by`
- `transition_reason`
- `history`

Future validation should allow these fields to be optional or nullable,
depending on the current lifecycle state and transition evidence:

- `previous_state`
- `review_gate_snapshot`
- `reviewer_verdict_snapshot`
- `manual_checkpoint_ref`
- `queue_summary`
- `dry_run_summary`
- `allowed_next_states`

Field rules:

- `updated_at` should be ISO-8601.
- `history` should be a list.
- `previous_state` may be null for the initial `draft` state.
- Optional evidence fields may be null only when the current state does not
  require that evidence.
- Unknown top-level fields may be allowed by a future schema version, but they
  must not replace required fields.

Current v0.3-C behavior: no schema validator is implemented.

## State Value Validation

Allowed states must match the v0.3-A state machine:

- `draft`
- `queued`
- `dry_run_ready`
- `awaiting_review`
- `blocked_by_reviewer`
- `approved_for_manual_run`
- `running`
- `completed`
- `failed`
- `cancelled`
- `archived`

Future validation should fail records with an unknown `state` value.

Future validation should also fail history entries, `previous_state`, and
`allowed_next_states` entries that reference unknown states.

Current v0.3-C behavior: unknown states are not validated because no state
record validator exists.

## Transition Validation

Future validation should allow only these direct transitions unless a later
policy explicitly extends the state machine:

| from | to |
| --- | --- |
| `draft` | `queued` |
| `queued` | `dry_run_ready` |
| `dry_run_ready` | `awaiting_review` |
| `awaiting_review` | `blocked_by_reviewer` |
| `awaiting_review` | `approved_for_manual_run` |
| `blocked_by_reviewer` | `awaiting_review` |
| `approved_for_manual_run` | `running` |
| `running` | `completed` |
| `running` | `failed` |
| `running` | `cancelled` |
| `completed` | `archived` |
| `failed` | `archived` |
| `cancelled` | `archived` |

Future validation should reject these forbidden transitions:

- `draft` -> `running`
- `queued` -> `running`
- `awaiting_review` -> `running`
- `blocked_by_reviewer` -> `running`
- `archived` -> `running`
- `completed` -> `running`
- `failed` -> `running` without explicit future retry policy
- `cancelled` -> `running` without explicit future restart policy

Additional v0.3-A inherited rule:

- `dry_run_ready` -> `running` should also be rejected because dry-run evidence
  does not imply execution approval.

Current v0.3-C behavior: no transition enforcement is implemented.

## Reviewer Gate Validation

Future validation should treat reviewer gate data as safety evidence, not as an
automatic approval source.

Rules:

- `review_gate: blocked_by_reviewer` should fail any future transition to
  `approved_for_manual_run` or `running`.
- `review_gate: open` should not automatically pass execution approval.
- `review_gate: unknown` should require operator review before approval.
- Reviewer verdict `pass` may support approval only with manual checkpoint
  evidence.
- Reviewer verdict `pass_with_notes` may support approval only with manual
  checkpoint evidence.
- Reviewer verdict `needs_work` should block approval in future enforcement.
- Reviewer verdict `blocked` should block approval in future enforcement.

Current v0.3-C behavior: no reviewer gate enforcement is implemented.

## Manual Checkpoint Reference Validation

Future validation should require a manual checkpoint reference before transition
to `approved_for_manual_run`.

Rules:

- Transition to `approved_for_manual_run` should require
  `manual_checkpoint_ref`.
- Override-like decisions should require a checkpoint note explaining who
  approved the decision, when it happened, and why it was accepted.
- The checkpoint must remain human-authored audit evidence.
- A checkpoint reference should point to the `Manual Review Checkpoints`
  section in `.hermes/plans/<plan_id>/log.md`.
- No automatic source-of-truth behavior is defined for checkpoint rows.

Current v0.3-C behavior: checkpoint references are not validated.

## Queue And Dry-Run Evidence Validation

Future validation should require evidence before moving through validation and
review preparation states.

Rules:

- Transition to `dry_run_ready` should require future dry-run evidence.
- Transition to `awaiting_review` should require reviewer report scaffold or
  reviewer evidence.
- `queue_summary` may include task count, next task, blocked task count, status
  counts, and parser warnings.
- `dry_run_summary` may include command, timestamp, result, selected task,
  blocked reasons, and artifacts.
- Dry-run evidence should not imply execution approval.
- Queue evidence should not imply reviewer approval.

Current v0.3-C behavior: no smoke script or validator is implemented for this
evidence.

## History Validation

Future validation should treat `history` as append-only audit evidence.

Each history item should include:

- `from`
- `to`
- `at`
- `by`
- `reason`
- `evidence`

Rules:

- Rewriting history entries should be invalid in a future validator.
- Deleting history entries should be invalid in a future validator.
- Corrective updates should be represented as new history entries.
- `history[*].at` should be ISO-8601.
- `history[*].from` and `history[*].to` should use known lifecycle states.
- The latest history item should match the record's current `state`.

Current v0.3-C behavior: no history validator is implemented.

## Archive And Finality Validation

Future validation should preserve final states for audit.

Rules:

- `archived` should be final for active operation.
- `archived` should not transition to `running`.
- `completed` should not transition to `running`.
- `failed` should not transition to `running` without explicit future retry
  policy and a new auditable retry record.
- `cancelled` should not transition to `running` without explicit future
  restart policy and a new auditable restart record.
- Archive transitions should preserve completion, failure, or cancellation
  evidence.

Current v0.3-C behavior: archive and finality rules are not enforced.

## Proposed Future Smoke Matrix

These are proposed smoke cases for a future validator or state transition
checker. Smoke scripts are not implemented in v0.3-C.

| case | future expected result | validation focus |
| --- | --- | --- |
| Valid `draft` state | PASS | Required fields, initial `previous_state`, empty or initial history. |
| Valid `queued` state | PASS | Known state, `draft` -> `queued`, queue evidence shape. |
| Valid `awaiting_review` with reviewer snapshot | PASS | Reviewer report scaffold/evidence exists and state is review-bound. |
| `blocked_by_reviewer` cannot approve | FAIL | Reviewer gate blocks `approved_for_manual_run`. |
| Unknown `review_gate` requires operator review | FAIL for approval | `unknown` cannot be treated as approval. |
| `archived` cannot transition to `running` | FAIL | Archive/finality rule. |
| Missing required field | FAIL | Schema validation. |
| Unknown state | FAIL | State value validation. |
| Invalid transition | FAIL | Transition graph validation. |
| History rewrite | FAIL | Append-only history validation. |

## Non-Goals

v0.3-C does not add:

- state.json validator implementation
- state.json generation
- state machine enforcement
- reviewer gate enforcement
- `run-all`
- automatic model routing
- automatic reviewer execution
- automatic push, merge, or deploy
- autonomous multi-task execution
- new runner behavior
- `run-next` behavior changes
- `plan-status` behavior changes
- Git tracking for `.hermes/`
