# Crack-CLI Benchmark Notes

These notes capture the Crack-CLI concepts Hermes should learn from without adopting the whole workflow in v0.1.

## Core Concepts

### `plan.md`

`plan.md` is the human-readable source of intent. It records the goal, scope, constraints, and task breakdown before execution starts. For Hermes, the useful pattern is to make the plan explicit and reviewable before any runner creates worktrees or invokes agents.

### `queue.md`

`queue.md` turns the plan into ordered work. Items can be ready, blocked, running, done, or marked for follow-up. Hermes v0.2 can borrow this as a lightweight queue file, but v0.1 remains a single-task runner.

### `log.md`

`log.md` is an append-only operator log. It gives each runner step a durable narrative that is easier to inspect than raw stdout alone. Hermes already has `hermes.log` and `journal.jsonl`; Crack-lite should keep machine state in JSON and human summaries in Markdown.

### `run-next`

`run-next` executes the next ready queue item, records the result, and stops. This is the safest Crack-style command for Hermes v0.2 because it preserves human control between units of work.

### `run-all`

`run-all` loops over ready queue items until the queue is empty, blocked, failed, or a configured limit is reached. Hermes should treat this as a later convenience on top of `run-next`, not the first implementation target.

### `pr-lock`

`pr-lock` serializes ownership of a pull request or branch so two agents do not edit or merge the same surface at the same time. Hermes can adopt the locking idea for local plan runs, but v0.1 and v0.2 should not push or merge.

### `needs_work`

`needs_work` marks a task that produced output but still requires repair, review, or another pass. This is more informative than a generic failure because it separates infrastructure failures from agent-produced work that is incomplete.

## Why Hermes Does Not Adopt Auto Merge Yet

Auto merge is intentionally out of scope for Hermes v0.1 and v0.2 Crack-lite. Hermes currently runs local worktrees, preserves artifacts, and prevents push, PR creation, merge, and deploy actions. Auto merge would require stronger guarantees first:

- trusted CI signal collection
- branch and PR ownership locks
- reviewer policy
- deterministic rollback or revert handling
- protection against stale base branches
- clear handling for `needs_work`

Until those controls exist, the correct boundary is local execution plus auditable artifacts. Humans keep merge authority.

## Hermes Takeaways

For v0.2 Crack-lite, Hermes should adopt the smallest useful subset:

- a reviewed plan file
- a queue file with explicit item status
- a Markdown execution log
- `run-next` as the primary runner
- a bounded `run-all` only after `run-next` is reliable
- local lock files before any multi-item runner
- `needs_work` as a first-class status

No auto merge, remote push, PR creation, deploy action, or Nous Hermes integration should be included in the v0.2 implementation.
