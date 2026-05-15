# Hermes Plan State Record Schema

This document defines the proposed design contract for a future Hermes plan
state record. It belongs to the v0.3-B documentation line.

v0.3-B documents the schema only. It does not add code enforcement, file
generation, validation, reviewer gate enforcement, `run-next` behavior changes,
or `plan-status` behavior changes.

## Purpose

The future plan state record should give Hermes one explicit place to record:

- the current lifecycle state of a plan
- the previous lifecycle state
- the evidence used when the state changed
- reviewer gate status at the time of the transition
- queue and dry-run evidence at the time of the transition
- append-only transition history for audit

This document is a design contract for that future record. It fixes the
candidate fields and evidence model before any state machine enforcement is
implemented.

## Proposed State Record Location

Future candidate location:

```text
.hermes/plans/<plan_id>/state.json
```

This location is proposed only. The current v0.3-B round does not create,
validate, require, or enforce this file.

`.hermes/` remains local runtime ignored state. This document does not make
`.hermes/` a Git-tracked directory.

## Proposed Top-Level Fields

| field | type | purpose |
| --- | --- | --- |
| `schema_version` | string | Version for the state record schema contract. |
| `plan_id` | string | Stable plan id matching `.hermes/plans/<plan_id>/`. |
| `state` | string | Current lifecycle state. |
| `previous_state` | string or null | Lifecycle state before the latest transition. |
| `updated_at` | string | Timestamp for the latest transition, expected to be ISO-8601. |
| `updated_by` | string | Human or future command identity that recorded the latest transition. |
| `transition_reason` | string | Short explanation for the latest transition. |
| `review_gate_snapshot` | object | Snapshot of the reviewer gate status at transition time. |
| `reviewer_verdict_snapshot` | object | Snapshot of the reviewer report verdict at transition time. |
| `manual_checkpoint_ref` | object or null | Reference to a human audit row in `log.md`, when applicable. |
| `queue_summary` | object | Queue evidence summarized from `queue.md`, when applicable. |
| `dry_run_summary` | object or null | Dry-run evidence summarized from `run-next --dry-run`, when applicable. |
| `allowed_next_states` | array of strings | Candidate direct next states from the current state. |
| `history` | array of objects | Append-only transition history. |

The field list is proposed. Hermes does not currently persist this record.

## State Field

The `state` field must align with the lifecycle states defined in
[PLAN_STATE_MACHINE.md](PLAN_STATE_MACHINE.md):

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

These state names are a proposed future contract. v0.3-B does not enforce them
in code.

## Review Gate Snapshot

`review_gate_snapshot.review_gate` should use one of these candidate values:

- `open`
- `blocked_by_reviewer`
- `unknown`

The snapshot records what `plan-status` and the plan-level reviewer report
showed at the time of a state transition. It is historical evidence, not an
automatic approval.

Rules for the future policy:

- `review_gate: open` is not automatic execution approval.
- `review_gate: blocked_by_reviewer` should prevent future transitions to
  `approved_for_manual_run` and `running`.
- `review_gate: unknown` should require operator inspection before approval.

Current v0.3-B behavior: there is no enforcement.

Candidate shape:

```json
{
  "review_gate": "open",
  "source": "plan-status",
  "captured_at": "2026-05-15T10:30:00Z"
}
```

## Reviewer Verdict Snapshot

`reviewer_verdict_snapshot` should record the current plan-level verdict from
`.hermes/plans/<plan_id>/reviewer_report.md` at transition time.

Candidate fields:

- `verdict`
- `source_path`
- `captured_at`
- `notes`

This snapshot should help explain why a state transition was allowed, blocked,
or returned to review in a future implementation. It does not replace the
reviewer report.

## Manual Checkpoint Reference

`manual_checkpoint_ref` is a reference to a row in the `Manual Review
Checkpoints` section of `.hermes/plans/<plan_id>/log.md`.

Its purpose is to connect a future state transition to a human-maintained audit
log entry.

It is not a source of truth for automatic decisions. Future enforcement should
use explicit policy and machine-readable evidence, while preserving this
reference for audit traceability.

Candidate fields:

- `source_path`
- `section`
- `checkpoint`
- `row_ref`
- `recorded_by`
- `recorded_at`

## Queue And Dry-Run Evidence

`queue_summary` is a candidate snapshot of `queue.md` state at transition time.
It can record:

- total task count
- count by task status
- next runnable task id
- blocked task ids
- parser warnings

`dry_run_summary` is a candidate snapshot of `run-next <plan_id> --dry-run`
output or validation results at transition time. It can record:

- command
- exit code
- selected runnable task id
- blocked reasons
- whether plan files were modified
- captured output path or short output summary

Both fields are documentation-only in v0.3-B. Hermes does not generate,
persist, or validate this evidence yet.

## History

`history` is the proposed append-only transition history.

Each history item should include:

- `from`
- `to`
- `at`
- `by`
- `reason`
- `evidence`

Principles:

- transition history should be append-only
- existing history entries should not be rewritten
- corrections should be recorded as new history entries
- failed, cancelled, and archived evidence should be preserved for audit

Candidate shape:

```json
{
  "from": "queued",
  "to": "dry_run_ready",
  "at": "2026-05-15T10:30:00Z",
  "by": "operator:founder_ys",
  "reason": "Queue reviewed and dry-run candidate inspected.",
  "evidence": {
    "queue_summary_ref": "state.queue_summary",
    "dry_run_summary_ref": "state.dry_run_summary"
  }
}
```

## Proposed Example JSON

This is a proposed example only. Hermes does not currently create this file.

```json
{
  "schema_version": "0.3-b-draft",
  "plan_id": "trader-d129-docs-only",
  "state": "awaiting_review",
  "previous_state": "dry_run_ready",
  "updated_at": "2026-05-15T10:30:00Z",
  "updated_by": "operator:founder_ys",
  "transition_reason": "Dry-run inspection completed; waiting for reviewer checkpoint before manual approval.",
  "review_gate_snapshot": {
    "review_gate": "open",
    "source": "plan-status",
    "captured_at": "2026-05-15T10:29:30Z"
  },
  "reviewer_verdict_snapshot": {
    "verdict": "pending",
    "source_path": ".hermes/plans/trader-d129-docs-only/reviewer_report.md",
    "captured_at": "2026-05-15T10:29:30Z",
    "notes": "Reviewer report exists; final review still pending."
  },
  "manual_checkpoint_ref": {
    "source_path": ".hermes/plans/trader-d129-docs-only/log.md",
    "section": "Manual Review Checkpoints",
    "checkpoint": "dry-run-reviewed",
    "row_ref": "checkpoint:dry-run-reviewed@2026-05-15",
    "recorded_by": "operator:founder_ys",
    "recorded_at": "2026-05-15T10:30:00Z"
  },
  "queue_summary": {
    "source_path": ".hermes/plans/trader-d129-docs-only/queue.md",
    "total_tasks": 3,
    "status_counts": {
      "pending": 2,
      "running": 0,
      "completed": 1,
      "needs_work": 0,
      "failed": 0,
      "skipped": 0
    },
    "next_task_id": "unit-002",
    "blocked_task_ids": [
      "unit-003"
    ],
    "parser_warnings": []
  },
  "dry_run_summary": {
    "command": "python3 hermes.py run-next trader-d129-docs-only --dry-run",
    "exit_code": 0,
    "selected_task_id": "unit-002",
    "blocked_reasons": {
      "unit-003": "dependency_not_completed:unit-002"
    },
    "modified_plan_files": false,
    "output_summary": "First runnable pending unit is unit-002."
  },
  "allowed_next_states": [
    "blocked_by_reviewer",
    "approved_for_manual_run"
  ],
  "history": [
    {
      "from": "draft",
      "to": "queued",
      "at": "2026-05-15T10:00:00Z",
      "by": "operator:founder_ys",
      "reason": "Initial queue authoring completed.",
      "evidence": {
        "queue_summary": {
          "total_tasks": 3,
          "parser_warnings": []
        }
      }
    },
    {
      "from": "queued",
      "to": "dry_run_ready",
      "at": "2026-05-15T10:20:00Z",
      "by": "operator:founder_ys",
      "reason": "Dry-run command found a runnable pending unit.",
      "evidence": {
        "dry_run_summary": {
          "selected_task_id": "unit-002",
          "exit_code": 0
        }
      }
    },
    {
      "from": "dry_run_ready",
      "to": "awaiting_review",
      "at": "2026-05-15T10:30:00Z",
      "by": "operator:founder_ys",
      "reason": "Dry-run inspection completed; waiting for reviewer checkpoint before manual approval.",
      "evidence": {
        "review_gate": "open",
        "manual_checkpoint_ref": "checkpoint:dry-run-reviewed@2026-05-15"
      }
    }
  ]
}
```

## Validation Rules Draft

These are future validation candidates only. v0.3-B does not implement them.

- `schema_version` is required.
- `plan_id` is required.
- `state` must be one of the known lifecycle states.
- `previous_state` can be null only for the initial `draft` state.
- `updated_at` should be ISO-8601.
- `updated_by` should identify the human operator or future command actor.
- `review_gate_snapshot.review_gate` should be `open`,
  `blocked_by_reviewer`, or `unknown`.
- `allowed_next_states` should match the allowed transition policy for the
  current state.
- `history` should be append-only.
- Existing history entries should not be rewritten.
- `archived` must not transition back to `running`.
- `blocked_by_reviewer` must not transition to `running` without a future
  explicit override policy.
- `review_gate: blocked_by_reviewer` should block transition to
  `approved_for_manual_run` and `running` in future enforcement.

## Non-Goals

This schema design does not add:

- state enforcement
- reviewer gate enforcement
- `run-all`
- automatic model routing
- automatic reviewer execution
- automatic push, merge, or deploy
- autonomous multi-task execution
- new runner behavior
- `run-next` behavior changes
- `plan-status` behavior changes
- generated `.hermes/` state files
- Git tracking for `.hermes/`
