# Hermes Agent OS Reference Stack

## Purpose

Hermes Agent OS is the safe execution kernel for AI-assisted development.

Its core role:
- validate task.yaml
- isolate work in git worktrees
- run Codex safely
- write state.json and journal.jsonl
- preserve logs
- cleanup owned runs
- block automatic push, merge, deploy by default

External projects are reference layers, not replacements.

## Layers

### 1. Core Kernel: hermes-agent-os

Owns:
- task validation
- risk policy
- worktree safety
- Codex execution
- state and journal artifacts
- cleanup safety

This remains the center of the system.

### 2. Plan Runner Reference: Crack-CLI

Useful ideas:
- split large work into small units
- plan.md
- queue.md
- log.md
- run-next
- run-all
- needs_work
- lock files

Adoption:
- implement Crack-lite inside hermes-agent-os v0.2
- use .hermes/plans instead of .crack
- do not adopt automatic merge, PR, push, or deployment yet

### 3. Workflow Pack Reference: oh-my-hermes

Useful ideas:
- CTO / PM / Dev / QA / Ops roles
- reusable skills
- workflow templates
- status reports

Adoption:
- do not install as-is for critical repos
- extract patterns into a YS-specific workflow pack
- avoid production shipping workflows for Trader-YS

### 4. Planning Reference: Hermes Agent Idea Workflow

Useful for:
- idea to design doc
- design doc to implementation spec
- implementation spec to agent handoff

Adoption:
- useful for CourseCheck, CosFan, Salon OS, AI Design Lab tools
- not directly used for Trader-YS critical implementation

### 5. Operator Hub: Nous Hermes Agent

Useful for:
- messenger gateway
- cron scheduling
- profiles
- memory/session recall
- model routing
- long-running supervisor

Adoption:
- later, as a supervisor layer
- initial integration must be CLI-only
- no Telegram/cron automation until local pipeline is stable

### 6. Memory Reference: PLUR

Useful for:
- project-scoped memory
- conventions
- recurring preferences

Adoption:
- no global memory by default
- no secrets, API keys, company confidential content, or trading credentials
- Trader-YS memory must remain policy-scoped and reviewed

### 7. Log Optimization: RTK Hermes

Useful for:
- token reduction
- compressed command output

Adoption:
- raw logs must always be preserved
- compressed summaries are context optimization only

### 8. Monitoring: hermesd / Hermes Desktop

Useful for:
- sessions
- cron jobs
- gateway status
- cost/token monitoring

Adoption:
- useful after Nous Hermes integration
- not required for v0.1/v0.2
