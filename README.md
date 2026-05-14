# Hermes Agent OS

Hermes v0 is a local single-task runner for safe Codex execution.

## v0 Goal

Read one task.yaml, validate it, create an isolated Git worktree, build prompt.md, optionally run codex exec, capture logs, save git outputs, append journal.jsonl, and write state.json.

## v0.1 Local Smoke Tests

Prefer the portable smoke script. It creates a temporary Git repository, task file, and runs root under `/tmp`, then runs the v0.1 non-nested smoke checks.

```bash
bash scripts/smoke_v0_1.sh
```

The script uses `python3 hermes.py run ... --no-codex`; it does not launch nested Codex.

`examples/trader-review.yaml` remains a machine-specific sample. If that repository path does not exist on the current machine, use the smoke script above or adjust a local-only copy before running manual validate/dry-run/run commands.

## v0.2-A Plan Scaffold

Hermes can create and inspect local Crack-lite plan scaffold directories without running Codex or executing queue units.

```bash
python3 hermes.py plan-init trader-d129-docs-only --title "Trader D129 docs-only review" --objective "Prepare a docs-only review plan"
python3 hermes.py plan-status trader-d129-docs-only
```

Generated `.hermes/` runtime plans are local artifacts and are ignored by Git. Do not commit generated `.hermes/plans/*` directories.
