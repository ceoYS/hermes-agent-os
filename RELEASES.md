# Hermes Release Ledger

This ledger records the completed Hermes v0.2 release line as of
`hermes-v0.2-g-review-workflow-docs-20260515`.

It is a closure document, not an execution plan. It does not introduce any
new runner behavior, automation, model routing, reviewer execution, push,
merge, or deploy capability.

## v0.2 Release Ledger

| version | tag | merge commit | summary | safety boundary |
| --- | --- | --- | --- | --- |
| v0.2-A | `hermes-v0.2-a-plan-scaffold-20260514` | `8f68746` | Added `.hermes/plans/<plan_id>/` plan scaffold through `plan-init` and `plan-status`. | Local scaffold only; no queue unit execution and generated `.hermes/` state remains ignored. |
| v0.2-B | `hermes-v0.2-b-queue-parser-20260514` | `8e5fbf6` | Added `queue.md` parsing and enhanced `plan-status` queue counts, units, and warnings. | Read-only parser/status reporting; no queue mutation or execution. |
| v0.2-C | `hermes-v0.2-c-run-next-dry-run-20260515` | `4ec81a8` | Added `run-next <plan_id> --dry-run` to identify the first runnable pending unit. | Dry-run inspection only; real `run-next` execution remains unimplemented. |
| v0.2-D | `hermes-v0.2-d-reviewer-report-20260515` | `215e150` | Added plan-level `reviewer_report.md` scaffold and verdict parsing in `plan-status`. | One report per plan only; no auto reviewer execution and no per-unit review files. |
| v0.2-E | `hermes-v0.2-e-review-gate-20260515` | `a1b5a26` | Added reviewer gate summary derived from the plan-level reviewer verdict. | Human-facing gate status only; no automatic merge, execution, or reviewer decision. |
| v0.2-F | `hermes-v0.2-f-review-checkpoint-log-20260515` | `af874b9` | Added plan-level `log.md` template with manual review checkpoint table. | Audit log only; not an automatic source of truth for Hermes decisions. |
| v0.2-G | `hermes-v0.2-g-review-workflow-docs-20260515` | `e5783c8` | Documented the manual review workflow in the README. | Documentation only; no execution expansion, model routing, run-all, or automation. |

## Current Capability Summary

At v0.2-G, Hermes has:

- plan scaffold
- queue parser
- plan-status
- run-next dry-run
- reviewer report scaffold
- reviewer gate summary
- manual review checkpoint log
- README review workflow docs

## Safety Boundaries Still Active

Hermes v0.2 still preserves these boundaries:

- no Codex execution expansion beyond existing behavior
- no run-all
- no model routing
- no auto push, merge, or deploy
- no auto reviewer execution
- no per-unit review files
- `.hermes/` remains local runtime ignored state

## Explicit Non-Goals

Hermes v0.2 is not yet an autonomous multi-task executor.

Hermes does not auto-select models.

Hermes does not auto-merge or auto-deploy.

Reviewer results remain human-authored and manually reviewed.

## Next Candidate Directions

Possible next directions should remain planning and safety work until they are
reviewed:

- v0.3 planning only
- safer plan lifecycle docs
- operator checklist
- task state machine design
- still avoid auto execution until reviewed
