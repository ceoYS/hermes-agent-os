#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

SMOKE_REPO="/tmp/hermes-v01-smoke-repo"
SMOKE_TASK="/tmp/hermes-v01-smoke-task.yaml"
SMOKE_RUNS="/tmp/hermes-v01-smoke-runs"

safe_rm() {
  local path="$1"
  case "$path" in
    /tmp/hermes-v01-smoke-*) rm -rf -- "$path" ;;
    *) echo "refusing to remove unexpected path: $path" >&2; exit 1 ;;
  esac
}

run() {
  echo "+ $*"
  "$@"
}

write_smoke_task() {
  cat > "$SMOKE_TASK" <<YAML
id: hermes-v01-smoke

repo_path: $SMOKE_REPO
base_branch: main
branch_prefix: agent/hermes-v01-smoke
runs_root: $SMOKE_RUNS

risk_level: critical
task_type: review

allow_edits: false
allow_push: false
allow_draft_pr: false

codex:
  model: gpt-5.5
  effort: high
  sandbox: read-only
  timeout_minutes: 1

limits:
  max_context_chars: 10000
  max_prompt_chars: 20000
  max_stdout_mb: 1
  max_stderr_mb: 1

context_files:
  - AGENTS.md

objective: |
  Review this temporary smoke-test repository.
  Do not modify files.

acceptance_criteria:
  - No files modified
  - Smoke run completes without nested Codex execution

test_commands: []
YAML
}

create_smoke_repo() {
  mkdir -p "$SMOKE_REPO"
  run git -C "$SMOKE_REPO" init
  run git -C "$SMOKE_REPO" checkout -B main
  run git -C "$SMOKE_REPO" config user.name "Hermes Smoke Test"
  run git -C "$SMOKE_REPO" config user.email "hermes-smoke@example.invalid"

  cat > "$SMOKE_REPO/AGENTS.md" <<'EOF'
# Smoke Test Repository

This temporary repository exists only for the Hermes v0.1 smoke test.
EOF

  run git -C "$SMOKE_REPO" add AGENTS.md
  run git -C "$SMOKE_REPO" commit -m "Initial smoke repository"
}

latest_run_id() {
  python3 - "$SMOKE_RUNS/journal.jsonl" <<'PY'
import json
import sys
from pathlib import Path

journal = Path(sys.argv[1])
last = None
with journal.open(encoding="utf-8") as handle:
    for line in handle:
        if line.strip():
            last = json.loads(line)
if not last or not last.get("run_id"):
    raise SystemExit("no run_id found in journal")
print(last["run_id"])
PY
}

assert_contains() {
  local path="$1"
  local needle="$2"
  if ! grep -Fq -- "$needle" "$path"; then
    echo "expected $path to contain: $needle" >&2
    exit 1
  fi
}

assert_not_contains() {
  local path="$1"
  local needle="$2"
  if grep -Fq -- "$needle" "$path"; then
    echo "expected $path not to contain: $needle" >&2
    exit 1
  fi
}

assert_empty_file() {
  local path="$1"
  if [[ -s "$path" ]]; then
    echo "expected empty file: $path" >&2
    exit 1
  fi
}

main() {
  cd "$REPO_ROOT"

  safe_rm "$SMOKE_REPO"
  safe_rm "$SMOKE_RUNS"
  safe_rm "$SMOKE_TASK"

  create_smoke_repo
  write_smoke_task

  run python3 -m py_compile hermes.py
  run python3 hermes.py --help
  run python3 hermes.py validate "$SMOKE_TASK"
  run python3 hermes.py dry-run "$SMOKE_TASK"
  run python3 hermes.py run "$SMOKE_TASK" --no-codex
  run python3 hermes.py list --runs-root "$SMOKE_RUNS"

  local run_id
  run_id="$(latest_run_id)"
  local run_dir="$SMOKE_RUNS/$run_id"

  run python3 hermes.py status "$run_id" --runs-root "$SMOKE_RUNS"
  run python3 hermes.py cleanup --dry-run --older-than 1m --runs-root "$SMOKE_RUNS"

  assert_contains "$run_dir/git_status_raw.txt" ".hermes-managed"
  assert_not_contains "$run_dir/git_status.txt" ".hermes-managed"
  assert_empty_file "$run_dir/git_diff.patch"
  assert_empty_file "$run_dir/git_branch_diff.patch"

  echo "Hermes v0.1 smoke test passed: $run_id"
}

main "$@"
