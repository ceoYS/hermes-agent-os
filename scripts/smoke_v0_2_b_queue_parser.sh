#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

SMOKE_PLAN_ID="smoke-queue-parser"
HERMES_ROOT="$REPO_ROOT/.hermes"
SMOKE_PLAN_DIR="$HERMES_ROOT/plans/$SMOKE_PLAN_ID"

run() {
  echo "+ $*"
  "$@"
}

safe_remove_smoke_plan() {
  local target="$1"
  case "$target" in
    "$REPO_ROOT/.hermes/plans/$SMOKE_PLAN_ID")
      if [[ -d "$target" ]]; then
        rm -f -- \
          "$target/plan.md" \
          "$target/queue.md" \
          "$target/log.md" \
          "$target/state.json" \
          "$target/morning_brief.md" \
          "$target/reviewer_report.md"
        rmdir -- "$target"
      fi
      ;;
    *)
      echo "refusing to remove unexpected path: $target" >&2
      exit 1
      ;;
  esac
}

assert_output_contains() {
  local output="$1"
  local needle="$2"
  if ! grep -Fq -- "$needle" <<<"$output"; then
    echo "expected plan-status output to contain: $needle" >&2
    exit 1
  fi
}

main() {
  cd "$REPO_ROOT"

  safe_remove_smoke_plan "$SMOKE_PLAN_DIR"

  run python3 -m py_compile hermes.py
  run python3 hermes.py plan-init "$SMOKE_PLAN_ID" \
    --title "Smoke Queue Parser" \
    --objective "Verify queue parser warnings and counts"

  cat > "$SMOKE_PLAN_DIR/queue.md" <<'EOF'
Queue notes before the table should be ignored.

| id | title | status | dependencies | notes |
| --- | --- | --- | --- | --- |
| unit-001 | Pending unit | pending | - | Pending note |
| unit-002 | Running unit | running | unit-001 | Running note |
| unit-003 | Completed unit | completed | unit-002 | Completed note |
| unit-004 | Needs work unit | needs_work | unit-003 | Needs work note |
| unit-005 | Failed unit | failed | unit-004 | Failed note |
| unit-006 | Skipped unit | skipped | unit-005 | Skipped note |
| unit-007 | Unknown unit | unknown_status | - | Unknown note |
| unit-001 | Duplicate unit | pending | - | Duplicate note |
| malformed | short |

Trailing notes after the table should be ignored.
EOF

  local output
  output="$(python3 hermes.py plan-status "$SMOKE_PLAN_ID")"
  printf '%s\n' "$output"

  assert_output_contains "$output" "pending"
  assert_output_contains "$output" "running"
  assert_output_contains "$output" "completed"
  assert_output_contains "$output" "needs_work"
  assert_output_contains "$output" "failed"
  assert_output_contains "$output" "skipped"
  assert_output_contains "$output" "unknown"
  assert_output_contains "$output" "warnings"

  safe_remove_smoke_plan "$SMOKE_PLAN_DIR"

  echo "Hermes v0.2-B queue parser smoke test passed"
}

main "$@"
