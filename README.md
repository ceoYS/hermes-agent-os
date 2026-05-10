# Hermes Agent OS

Hermes v0 is a local single-task runner for safe Codex execution.

## v0 Goal

Read one task.yaml, validate it, create an isolated Git worktree, build prompt.md, optionally run codex exec, capture logs, save git outputs, append journal.jsonl, and write state.json.
