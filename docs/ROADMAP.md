# Hermes Agent OS Roadmap

## Current Status

v0 local kernel is complete.

Completed:
- validate
- dry-run
- run --no-codex
- run --execute
- cleanup
- GitHub push
- success tag: hermes-v0-local-success-20260510

## v0.1 — Kernel Hardening

Goal:
Make v0 reliable enough for repeated local execution.

Scope:
1. Wire task.codex.effort into actual Codex CLI config.
2. Split git status artifacts into raw and filtered forms.
3. Add list command.
4. Add status <run_id> command.
5. Improve README smoke tests.
6. Preserve existing safety policy.

Non-scope:
- no parallel execution
- no Nous Hermes integration
- no Crack-lite implementation yet
- no auto push
- no auto merge
- no auto deploy

## v0.2 — Crack-lite Plan Runner

Goal:
Adopt the useful parts of Crack-CLI.

Concepts:
- plan.md
- queue.md
- log.md
- run-next
- run-all
- needs_work
- lock file

Planned structure:

.hermes/
  inbox.md
  plans/
    <plan-id>/
      plan.md
      queue.md
      log.md
      state.json
      morning_brief.md
      reviewer_report.md

Planned commands:
- hermes submit
- hermes plan
- hermes run-next
- hermes run-all
- hermes plan-status

Safety:
- one unit at a time
- worktree per unit
- no auto merge
- no auto push
- no auto deploy
- stop on reviewer needs_work or blocked verdicts

v0.2-D status:
- plan-level reviewer_report.md scaffold added
- plan-status surfaces reviewer verdicts and stop signals
- per-unit review files are not implemented yet

## v0.3 — Planner / Builder / Reviewer Pipeline

Goal:
Turn a user request into a staged file-based workflow.

Roles:
- Planner: convert request into plan.md and queue.md
- Builder: execute one queue unit through Hermes Agent OS
- Reviewer: inspect diff, logs, and test outputs
- Supervisor: create morning_brief.md

## v0.4 — Nightly Queue

Goal:
Run multiple plans overnight with a clear morning report.

Scope:
- nightly.yaml
- max tasks
- max runtime minutes
- stop on critical failure
- consolidated morning_brief.md

## v0.5 — Nous Hermes CLI-only POC

Goal:
Allow Nous Hermes Agent to call Hermes Agent OS commands.

Scope:
- CLI-only integration
- no Telegram yet
- no cron yet
- no multi-profile automation yet

## v1.0 — Multi-project Agent Operations

Candidate projects:
- Trader-YS
- Hermes Agent OS
- CourseCheck
- CosFan
- Salon OS
- PREMOIRE research
- AI Design Lab guide automation
