# Hermes Agent OS

Hermes v0 is a local single-task runner for safe Codex execution.

## v0 Goal

Read one task.yaml, validate it, create an isolated Git worktree, build prompt.md, optionally run codex exec, capture logs, save git outputs, append journal.jsonl, and write state.json.

## v0.1 Local Smoke Tests

Note: `examples/trader-review.yaml` contains a machine-specific sample path.
If that repository path does not exist on the current machine, create a temporary smoke task or adjust a local-only copy before running validate/dry-run/run.

```bash
python3 -m py_compile hermes.py
python3 hermes.py --help
python3 hermes.py validate examples/trader-review.yaml
python3 hermes.py dry-run examples/trader-review.yaml
python3 hermes.py run examples/trader-review.yaml --no-codex
python3 hermes.py list
python3 hermes.py status <latest_run_id>
python3 hermes.py cleanup --dry-run --older-than 1m
```

Do not use `run --execute` for this smoke test unless you explicitly want to launch a nested Codex session.
