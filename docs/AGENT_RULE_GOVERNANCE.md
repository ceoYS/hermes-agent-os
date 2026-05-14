# Agent Rule Governance

## Problem

Agent instruction files can become too large.

When rules are treated as a wishlist, compliance drops. The useful model is:
- keep only rules tied to observed failures
- keep the root instruction file short
- move project details into referenced docs
- enforce deterministic rules in code, not prompts

## Policy

Hermes Agent OS must not rely on long prompt rules alone.

Rules are split into four layers:

1. Root behavioral contract
2. Project policy
3. Task-local constraints
4. Deterministic code gates

## Layer 1 — Root Behavioral Contract

Keep root agent instructions under 120 lines when possible.

Required principles:
1. Think before acting.
2. Keep changes simple.
3. Make surgical edits.
4. Define success criteria.
5. Use models only for judgment calls.
6. Respect token and runtime budgets.
7. Surface conflicts instead of blending patterns.
8. Read before writing.
9. Verify intent, not just behavior.
10. Checkpoint after significant steps.
11. Match existing conventions.
12. Fail loud.

Do not expand this section with project-specific details.

## Layer 2 — Project Policy

Project-specific rules live in docs or module-local instruction files.

Examples:
- Trader-YS risk rules
- allowed file paths
- test commands
- forbidden changes
- module boundaries

## Layer 3 — Task-local Constraints

Each task.yaml must state:
- objective
- acceptance criteria
- allow_edits
- allow_push
- allow_draft_pr
- risk_level
- context_files
- token and output limits

Task-local constraints override broad preferences but cannot weaken safety policy.

## Layer 4 — Deterministic Code Gates

The following must be enforced by code, not by model compliance:
- dirty repo check
- forbidden context path check
- symlink context rejection
- max prompt chars
- max stdout/stderr size
- timeout
- no danger-full-access
- no push in v0
- no draft PR in v0
- cleanup ownership checks

## Rule Compression Strategy

Do not paste every reference into CLAUDE.md.

Instead:
- root instruction file contains only behavioral rules
- docs/REFERENCE_STACK.md contains external tool evaluation
- docs/ROADMAP.md contains implementation order
- docs/V0_2_CRACK_LITE_PLAN.md contains plan runner design
- task.yaml contains execution-specific constraints

## Success Criteria

A good instruction system is:
- short enough to be read every run
- specific enough to prevent known failures
- backed by code gates
- auditable through state.json and journal.jsonl
- recoverable through checkpoints
