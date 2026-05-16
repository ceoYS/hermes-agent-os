# Hermes v0.4 Entry Criteria

Hermes v0.4 must start from the v0.3 safety boundary. The next release line may
improve auditability, reproducibility, and operator-facing reporting, but it
must not silently turn read-only validation into enforcement.

## Purpose

This document defines the conditions required before v0.4 work begins and the
boundaries that remain prohibited at v0.4 entry.

It is an entry criteria document, not an implementation plan.

## Candidate v0.4 Scope

v0.4 may consider:

- auditability improvements
- reproducibility improvements
- operator-facing documentation improvements
- read-only reporting improvements
- UX or documentation improvements that make validation results easier to
  interpret

These candidates must preserve the v0.3 read-only boundary unless a later round
explicitly approves a different design.

## Entry Conditions

Before v0.4 work begins:

- v0.3-A through v0.3-I must be merged to `main`.
- The v0.3-J release ledger must be merged to `main`.
- All existing smoke checks must pass.
- The working tree must be clean.
- README and documentation links must not be broken.
- The read-only boundary for `validate-state` must be clear in the docs.
- The Level 1 informational boundary for `plan-status` state validation must be
  clear in the docs.
- `.hermes/` must remain ignored local runtime state.

## Still Prohibited At v0.4 Entry

The following remain prohibited unless a future approved design explicitly
changes them:

- `run-next` enforcement
- state machine enforcement
- reviewer gate enforcement
- automatic state transition
- `state.json` auto repair, creation, or update
- auto reviewer execution
- auto push, merge, or deploy
- `run-all`
- model routing

## Requirements Before Enforcement

Any proposal to introduce enforcement must first include:

- a separate design document
- explicit approval
- threat and safety review
- rollback plan
- dedicated tests
- staged rollout plan

Until those prerequisites are satisfied, validation output remains
operator-facing information only.

## v0.4 Readiness Checklist

Use this checklist before opening v0.4 implementation work:

- v0.3 closure docs reviewed
- v0.3-J release ledger reviewed
- existing smoke checks passed
- working tree clean
- README and docs links checked
- read-only validation boundaries preserved
- no code behavior changed unless explicitly approved in a future round

## Non-Goals

This document is not:

- an execution feature implementation plan
- a `run-next` integration plan
- an enforcement approval document
- a state machine enforcement policy
- a reviewer gate enforcement policy
- authorization for automatic reviewer execution, push, merge, or deploy

v0.4 entry starts with documentation and reporting discipline. It does not
grant execution authority to validation results.
