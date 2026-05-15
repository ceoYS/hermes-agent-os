# Hermes v0.3 Entry Criteria

Hermes v0.3 must not start by expanding execution. Before v0.3 considers task
lifecycle execution, reviewer gate enforcement, or state transitions, the human
operator must approve the operating model described here.

## Entry Conditions

Before v0.3 execution work begins:

- v0.2 documentation and smoke checks must be green on `main`.
- The current release tag must point at the intended `main` commit.
- The working tree must be clean before any new v0.3 branch is created.
- `.hermes/` must remain ignored local runtime state.
- Existing `plan-init`, `plan-status`, and `run-next --dry-run` behavior must be
  preserved unless a v0.3 proposal explicitly changes it.
- v0.3 scope must be reviewed as design first, then implementation.

## Required Designs

The v0.3 line needs written design decisions before implementation:

- state machine design
- plan lifecycle definition
- failure, retry, and cancel policy
- reviewer gate enforcement policy
- operator override policy
- run-all prohibition or strict limitation conditions
- auto push, merge, and deploy prohibition or separate approval conditions

These decisions should be documented before adding new runner capability.

## State Machine

v0.3 needs an explicit state machine for queue units and plans.

At minimum, the design should define:

- allowed states
- allowed transitions
- terminal states
- blocked states
- which command can create each transition
- which transitions require human confirmation
- where state is persisted
- how invalid or unknown state is reported

No command should infer an irreversible state transition from free-form notes.

## Plan Lifecycle

v0.3 needs a plan lifecycle before execution expands beyond dry-run inspection.

At minimum, define:

- plan creation
- queue authoring and review
- runnable unit selection
- unit execution start
- unit execution completion
- reviewer review
- needs_work handling
- plan completion
- plan cancellation
- audit log requirements

The lifecycle must keep human review visible at each irreversible step.

## Failure, Retry, And Cancel Policy

v0.3 needs a failure model before any real queue execution is added.

At minimum, define:

- what counts as command failure
- what counts as Codex failure
- what counts as reviewer failure
- retry limits
- retry idempotency expectations
- retry artifact naming
- cancel behavior while a unit is running
- cancel behavior after a partial failure
- how failed or cancelled worktrees are preserved for audit

Retries must not silently hide failed attempts.

## Reviewer Gate Enforcement

v0.2 only reports `review_gate`. v0.3 must define when and how Hermes should
enforce it before enforcement is implemented.

At minimum, define:

- which commands are blocked by `needs_work` or `blocked`
- whether `pending` is allowed to proceed
- whether `pass_with_notes` is allowed to proceed
- how stale reviewer reports are detected
- how manual overrides are recorded
- whether enforcement applies per plan only or later per unit

Until this policy is approved, reviewer gate enforcement remains manual.

## Operator Override Policy

v0.3 needs an override policy before any command can bypass a safety gate.

At minimum, define:

- which gates can be overridden
- who is allowed to override
- whether override needs a command flag
- what reason text is required
- where the override is logged
- whether override applies once or persists
- how override is surfaced in `plan-status`

Overrides must be explicit and auditable.

## run-all Policy

`run-all` remains prohibited unless v0.3 defines strict limits first.

A future `run-all` proposal must define:

- maximum units per invocation
- maximum runtime
- stop conditions
- reviewer stop behavior
- retry behavior
- lock behavior
- audit output
- operator confirmation requirements

Without these limits, `run-all` must remain unavailable.

## Push, Merge, And Deploy Policy

Hermes must continue to prohibit automatic push, merge, and deploy by default.

Any future exception must require a separate approved design covering:

- exact allowed command
- target repository and branch constraints
- required clean working tree checks
- required smoke or test checks
- required reviewer verdict
- required human confirmation
- rollback or recovery instructions
- audit log entry

There is no implicit approval for auto push, auto merge, or auto deploy in v0.3.

## Explicit Non-Goals

Hermes is not yet an autonomous multi-task executor.

Hermes does not auto-route models.

Hermes does not auto-run reviewers.

Hermes does not auto-push, auto-merge, or auto-deploy.

Hermes does not enforce reviewer gates automatically yet.

Manual Review Checkpoints remain human-authored audit logs.

## Safety Boundaries

These boundaries remain active at v0.3 entry:

- no Codex execution expansion without an approved v0.3 design
- no run-all
- no model routing
- no auto push, merge, or deploy
- no auto reviewer execution
- no per-unit review files
- `.hermes/` remains local runtime ignored state
