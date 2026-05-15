# Hermes Plan State Machine

This document defines the proposed Hermes v0.3 plan lifecycle state machine.
It is a design document for v0.3-A.

## Current Implementation Boundary

Hermes v0.3-A is documentation only.

Currently implemented behavior remains unchanged:

- `plan-init` creates local plan scaffold files.
- `plan-status` reports queue, reviewer report, and `review_gate` status.
- `run-next <plan_id> --dry-run` inspects the next runnable pending unit.
- Hermes does not persist a plan lifecycle state field yet.
- Hermes does not enforce this state machine yet.
- Hermes does not enforce reviewer gates automatically yet.

All states and transitions below are proposed operating rules for future
implementation. They are not current code behavior.

## Actors

- Operator: the human owner of the plan and the only actor allowed to approve,
  cancel, archive, or override safety gates.
- Reviewer: a human or external reviewer that records review findings in
  `reviewer_report.md`; reviewer output can block progress but does not run
  work.
- Hermes command: a future CLI implementation that may validate, persist, or
  report state transitions after the policy is implemented.

## Plan State Definitions

| state | meaning | who can change it | intended transition type |
| --- | --- | --- | --- |
| `draft` | The plan exists but is still being authored. Queue units, objective, or review expectations may be incomplete. | Operator; future `plan-init` may create this initial state. | Manual creation or edit checkpoint. |
| `queued` | The plan queue has been authored and is ready for non-executing validation. It is not yet approved for execution. | Operator after queue review; future validation command may confirm it. | Manual promotion after queue authoring. |
| `dry_run_ready` | The queue has a runnable pending unit according to dry-run inspection, or the operator has confirmed that dry-run inspection can be performed. No execution approval is implied. | Operator or future dry-run/status validation command. | Validation-derived, but still non-executing. |
| `awaiting_review` | The plan or next unit is waiting for reviewer inspection before any manual run approval. | Operator after dry-run inspection; future command may move here after required artifacts exist. | Manual or validation-assisted checkpoint. |
| `blocked_by_reviewer` | Reviewer findings indicate `needs_work` or `blocked`; the plan must not proceed to approval or running. | Reviewer verdict update, surfaced by operator or future status validation. | Reviewer-derived blocking checkpoint. |
| `approved_for_manual_run` | The operator has explicitly approved a manual run after checking dry-run output and reviewer status. This is not autonomous execution approval. | Operator only. | Manual approval checkpoint. |
| `running` | A future runner has started the approved unit or plan action. v0.3-A does not implement this state. | Future Hermes runner after explicit operator action. | Command-driven after manual approval. |
| `completed` | The approved run finished successfully and required artifacts are recorded. | Future Hermes runner or operator after verifying completion evidence. | Result-derived terminal state. |
| `failed` | The approved run failed, partially completed, or produced invalid or missing required artifacts. | Future Hermes runner or operator after reviewing failure evidence. | Result-derived terminal state pending retry or archive. |
| `cancelled` | The operator intentionally stopped or abandoned the active or pending plan. | Operator only. | Manual terminal state. |
| `archived` | The plan is closed for active operation and retained only for audit/history. | Operator only. | Manual archival terminal state. |

The "intended transition type" column describes the future policy. In v0.3-A,
Hermes does not persist or enforce these state changes.

## Allowed Transitions

The future state machine should allow only these direct transitions unless a
separate policy explicitly extends it:

| from | to | reason |
| --- | --- | --- |
| `draft` | `queued` | Operator finishes initial queue authoring. |
| `queued` | `dry_run_ready` | Queue is ready for dry-run inspection or dry-run validation has found a candidate. |
| `dry_run_ready` | `awaiting_review` | Dry-run inspection is complete and review is required before approval. |
| `awaiting_review` | `blocked_by_reviewer` | Reviewer verdict is `needs_work` or `blocked`. |
| `awaiting_review` | `approved_for_manual_run` | Operator confirms reviewer status and manually approves a run. |
| `blocked_by_reviewer` | `awaiting_review` | Required fixes are made and the plan returns to review. |
| `approved_for_manual_run` | `running` | A future runner starts only after explicit operator approval. |
| `running` | `completed` | Execution succeeds and artifacts are recorded. |
| `running` | `failed` | Execution fails or required artifacts are invalid or missing. |
| `running` | `cancelled` | Operator cancels an active run. |
| `completed` | `archived` | Operator closes a completed plan for audit history. |
| `failed` | `archived` | Operator closes a failed plan without retrying in place. |
| `cancelled` | `archived` | Operator closes a cancelled plan for audit history. |

Retries from `failed` should not reuse the same transition silently. A retry
must create a new checkpoint or run record before returning to an executable
state.

## Forbidden Transitions

These direct transitions are forbidden by policy and should be rejected by
future enforcement:

- `draft` -> `running`
- `queued` -> `running`
- `dry_run_ready` -> `running`
- `awaiting_review` -> `running` without explicit operator approval
- `blocked_by_reviewer` -> `approved_for_manual_run`
- `blocked_by_reviewer` -> `running`
- `completed` -> `running`
- `failed` -> `running` without a new retry checkpoint or run record
- `cancelled` -> `running`
- `archived` -> `running`

General forbidden principles:

- No state may skip reviewer review when review is required.
- No state may imply approval from dry-run output alone.
- No terminal state may return to `running` without a new auditable record.
- No archived plan may become active again.

## Reviewer Gate Relationship

The v0.2 reviewer gate remains a status summary, not an enforcement mechanism.
Future enforcement should map it into the plan lifecycle as follows:

- `review_gate: blocked_by_reviewer` should prevent transition to
  `approved_for_manual_run` and `running`.
- `review_gate: open` does not automatically mean the plan is safe to run. The
  operator must still review the plan, dry-run output, queue dependencies, and
  checkpoint log.
- `review_gate: unknown` requires operator review before approval. It should not
  be treated as passing or non-blocking.

Current v0.3-A behavior: `plan-status` reports `review_gate`, but Hermes does
not block commands based on it.

## Operator Override Policy Draft

Overrides are prohibited by default.

If an exceptional override is required in a future implementation:

- the operator must record the reason in `log.md` under
  `Manual Review Checkpoints`;
- the override must require a separate explicit approval flag or policy;
- the override must be visible in future status output;
- the override must apply only to the specific checkpoint or run it approved;
- automatic override is forbidden.

v0.3-A does not implement override flags or override enforcement.

## Failure, Retry, And Cancel Policy Draft

`failed` means the run did not produce trustworthy successful completion. This
can include command failure, Codex failure, reviewer failure, missing artifacts,
invalid artifacts, or an operator-detected safety issue.

Retry policy draft:

- Retry must create a new checkpoint or new run record.
- Retry must preserve the failed attempt for audit.
- Retry must not erase or silently replace failure evidence.
- Retry automation is not implemented in v0.3-A.

Cancel policy draft:

- Cancel is an operator action only.
- Future cancellation must record who cancelled, when, and why.
- Cancelled plans cannot proceed to `running`.
- Cancel automation is not implemented in v0.3-A.

## Non-Goals

This state machine design does not add:

- `run-all`
- automatic model routing
- automatic reviewer execution
- automatic push, merge, or deploy
- automatic reviewer gate enforcement yet
- autonomous multi-task execution
- new runner behavior
- queue mutation behavior
- plan-status behavior changes
- run-next behavior changes

## Future Implementation Notes

These are implementation candidates only. They are not part of v0.3-A.

Future plan state file candidates:

- `.hermes/plans/<plan_id>/state.json`
- a `state:` field in a plan metadata file
- append-only state events in `.hermes/plans/<plan_id>/log.md`

Future status validation candidates:

- reject unknown lifecycle states
- report current lifecycle state in `plan-status`
- report invalid state transitions without mutating files
- compare lifecycle state with `review_gate`
- warn when `review_gate: unknown` exists before approval

Future smoke coverage candidates:

- initial plan state scaffold smoke
- allowed transition validation smoke
- forbidden transition rejection smoke
- reviewer gate blocks approval smoke
- failed retry requires new checkpoint smoke
- cancelled and archived plans cannot run smoke

Future CLI command candidates:

- `plan-state <plan_id>`
- `plan-transition <plan_id> <state>`
- `plan-approve <plan_id> --manual`
- `plan-cancel <plan_id> --reason "<reason>"`
- `plan-archive <plan_id>`

Any future command must be designed and reviewed before implementation, and must
preserve the existing v0.2 safety boundaries unless explicitly changed by an
approved v0.3 policy.
