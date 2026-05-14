# v0.2 Crack-lite Plan Runner

## Why

Long Codex loops can create context rot and hard-to-review code.

The safer pattern:
1. split work into small units
2. execute one unit at a time
3. checkpoint after each unit
4. stop on needs_work
5. preserve artifacts for review

Crack-CLI is a useful reference because it introduces a plan/queue/log model for Codex work.

Hermes Agent OS will adopt the pattern, not the full tool.

## Concepts to Adopt

### plan.md

Human-readable plan:
- objective
- constraints
- non-goals
- risk level
- ordered units
- acceptance criteria

### queue.md

Structured list of units:
- id
- title
- status
- dependencies
- task yaml path
- expected output
- reviewer checks

### log.md

Append-only execution log:
- unit started
- command run
- state path
- result
- reviewer verdict
- needs_work reason if any

### run-next

Execute exactly one pending unit.

### run-all

Repeat run-next until:
- queue complete
- a unit fails
- reviewer returns needs_work
- runtime budget exceeded

### needs_work

Reviewer status that stops the queue and asks for human or planner intervention.

## Not Adopted Yet

- automatic merge
- automatic PR creation
- automatic remote branch push
- automatic conflict resolution
- production deployment

## Proposed Directory

.hermes/
  plans/
    trader-d129-docs-only/
      plan.md
      queue.md
      log.md
      state.json
      morning_brief.md

## First Test Plan

Trader-YS docs-only review plan.

Requirements:
- no src diff
- no tests diff unless explicitly requested
- no config diff
- no push
- no merge
- no live readiness claim
