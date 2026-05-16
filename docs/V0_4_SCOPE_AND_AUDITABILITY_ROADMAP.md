# Hermes v0.4 Scope and Auditability Roadmap

Hermes v0.4 begins from the v0.3 read-only safety boundary. v0.4 focuses on
auditability, reproducibility, and operator-facing reporting. v0.4 does not
introduce enforcement, automation, or execution authority. This document is a
scope/roadmap document, not an implementation plan.

## Purpose

This document:

- narrows the v0.4 candidate scope listed in
  `docs/V0_4_ENTRY_CRITERIA.md`
- defines what auditability means in Hermes terms
- defines what reproducibility means in Hermes terms
- defines what operator-facing reporting means in Hermes terms
- preserves the v0.3 prohibition wall

Reference documents:

- `docs/V0_4_ENTRY_CRITERIA.md`
- `docs/RELEASE_LEDGER_V0_3.md`

## v0.4 In-Scope Buckets

Auditability:
Make it possible for a human operator to reconstruct, after the fact, what
Hermes observed, validated, or surfaced about a plan. No new mutation and no
new automation. Read-only artifact production, richer summary text, or
structured read-only logs may be considered.

Reproducibility:
Make Hermes commands deterministic enough that the same inputs produce the same
operator-facing output. May include version stamps, input fingerprints, or
validator input recording in docs/examples. Must not silently rewrite plan
files.

Operator-facing reporting:
Improve `plan-status`, `validate-state`, README guidance, and supporting docs so
an operator can interpret validation results faster. No exit code semantics
change. No new gating.

Documentation clarity:
Additional usage guides, examples, and interpretation docs that lower the chance
of operator misinterpretation. Pure docs only.

Each bucket inherits the v0.3 read-only boundary.

## v0.4 Out-of-Scope / Deferred Past v0.4

v0.4 will not:

- wire validation into `run-next`
- enforce state machine transitions
- enforce reviewer gates
- mutate, create, repair, or transition `state.json`
- execute reviewers automatically
- run `run-all`
- push, merge, or deploy automatically
- introduce model routing
- change `validate-state` exit code semantics
- change `plan-status` exit code semantics
- promote `state_validation` from informational to gating
- promote `review_gate` from informational to gating

Any of the above requires a separate design round, safety review, rollback plan,
dedicated tests, and staged rollout.

## Auditability Definition

Auditability means a clear human-readable trail of which validation was run,
against what input, and with what result. It means the ability for an operator
to reread that trail without rerunning the validator. Auditability uses
read-only artifacts only and does not include auto-generated state mutations.

Auditability in v0.4 is operator-facing, not machine-enforcing.

## Reproducibility Definition

Reproducibility means running the same Hermes read-only command against the same
`state.json` / plan inputs returns the same human-readable verdict and same
fields, modulo timestamps.

This is about output stability, not about regenerating runtime state.

## Operator-Facing Reporting Definition

Operator-facing reporting means any change to text the operator reads, such as
`plan-status` output, `validate-state` output, README quickstart sections, or
interpretation docs, that helps the operator make a faster and safer human
decision.

This excludes:

- new gating
- new exit code semantics
- new automation

## Candidate Round Layout for v0.4

Every entry below is a candidate round, not a committed round.

| candidate round | candidate scope | safety boundary note |
| --- | --- | --- |
| v0.4-A | scope and auditability roadmap doc | preserves the v0.3 read-only boundary; no enforcement; no automation; no run-next wiring |
| v0.4-B | auditability definition deep-dive doc | preserves the v0.3 read-only boundary; no enforcement; no automation; no run-next wiring |
| v0.4-C | reproducibility definition deep-dive doc | preserves the v0.3 read-only boundary; no enforcement; no automation; no run-next wiring |
| v0.4-D | operator-facing reporting surface inventory, read-only | preserves the v0.3 read-only boundary; no enforcement; no automation; no run-next wiring |
| v0.4-E | `validate-state` output stability spec, docs | preserves the v0.3 read-only boundary; no enforcement; no automation; no run-next wiring |
| v0.4-F | `plan-status` output stability spec, docs | preserves the v0.3 read-only boundary; no enforcement; no automation; no run-next wiring |
| v0.4-G | read-only audit trail format spec, docs | preserves the v0.3 read-only boundary; no enforcement; no automation; no run-next wiring |
| v0.4-H | operator interpretation upgrades for existing read-only outputs | preserves the v0.3 read-only boundary; no enforcement; no automation; no run-next wiring |
| v0.4-I | v0.4 release ledger | preserves the v0.3 read-only boundary; no enforcement; no automation; no run-next wiring |
| v0.4-J | v0.5 entry criteria | preserves the v0.3 read-only boundary; no enforcement; no automation; no run-next wiring |

## Round Acceptance Rules

Every v0.4 round must:

- pass existing smoke checks
- keep the working tree clean after merge
- not break README or docs links
- not modify `validate-state` exit code semantics
- not modify `plan-status` exit code semantics
- not modify `.hermes/` runtime state behavior
- include an explicit "no enforcement introduced" line in its PR

## Non-Goals

This document is not:

- an execution feature implementation plan
- a `run-next` integration plan
- an enforcement approval document
- a state machine enforcement policy
- a reviewer gate enforcement policy
- authorization for automatic reviewer execution, push, merge, or deploy
- a commitment that every listed candidate round will ship

## Closure Statement

v0.4-A narrows the v0.4 candidate scope to auditability, reproducibility, and
operator-facing reporting under the v0.3 read-only boundary. v0.4-A introduces
no code change, no automation, and no enforcement.
