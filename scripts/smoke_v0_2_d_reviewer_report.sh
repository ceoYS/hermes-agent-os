#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

SMOKE_ROOT="$(mktemp -d /tmp/hermes-v02d-smoke.XXXXXX)"
SMOKE_PLAN_ID="smoke-reviewer-report"
SMOKE_PLAN_DIR="$SMOKE_ROOT/.hermes/plans/$SMOKE_PLAN_ID"

cleanup() {
  case "$SMOKE_ROOT" in
    /tmp/hermes-v02d-smoke.*) rm -rf -- "$SMOKE_ROOT" ;;
    *) echo "refusing to remove unexpected path: $SMOKE_ROOT" >&2; exit 1 ;;
  esac
}

run() {
  echo "+ $*"
  "$@"
}

assert_file_exists() {
  local path="$1"
  if [[ ! -f "$path" ]]; then
    echo "expected file to exist: $path" >&2
    exit 1
  fi
}

assert_output_contains() {
  local output="$1"
  local needle="$2"
  if ! grep -Fq -- "$needle" <<<"$output"; then
    echo "expected output to contain: $needle" >&2
    exit 1
  fi
}

assert_repo_hermes_status_clean() {
  local output
  output="$(git -C "$REPO_ROOT" status --short -- .hermes)"
  if [[ -n "$output" ]]; then
    echo "expected repo .hermes/ to be ignored by git status, got:" >&2
    printf '%s\n' "$output" >&2
    exit 1
  fi
}

main() {
  trap cleanup EXIT
  cd "$SMOKE_ROOT"

  run python3 -m py_compile "$REPO_ROOT/hermes.py"
  run python3 "$REPO_ROOT/hermes.py" --help
  run python3 "$REPO_ROOT/hermes.py" plan-init "$SMOKE_PLAN_ID" \
    --title "Smoke Reviewer Report" \
    --objective "Verify reviewer report scaffold"

  assert_file_exists "$SMOKE_PLAN_DIR/plan.md"
  assert_file_exists "$SMOKE_PLAN_DIR/queue.md"
  assert_file_exists "$SMOKE_PLAN_DIR/log.md"
  assert_file_exists "$SMOKE_PLAN_DIR/state.json"
  assert_file_exists "$SMOKE_PLAN_DIR/morning_brief.md"
  assert_file_exists "$SMOKE_PLAN_DIR/reviewer_report.md"

  local output
  output="$(python3 "$REPO_ROOT/hermes.py" plan-status "$SMOKE_PLAN_ID")"
  printf '%s\n' "$output"
  assert_output_contains "$output" "reviewer_report:"
  assert_output_contains "$output" "- exists: yes"
  assert_output_contains "$output" "verdict: pending"
  assert_output_contains "$output" "status: not_yet_reviewed"
  assert_output_contains "$output" "stop_signal: no"

  printf '# Reviewer Report\n\nverdict: needs_work\n' > "$SMOKE_PLAN_DIR/reviewer_report.md"
  output="$(python3 "$REPO_ROOT/hermes.py" plan-status "$SMOKE_PLAN_ID")"
  printf '%s\n' "$output"
  assert_output_contains "$output" "verdict: needs_work"
  assert_output_contains "$output" "status: stop_signal"
  assert_output_contains "$output" "stop_signal: yes"
  assert_output_contains "$output" "plan should not proceed until reviewed and fixed"

  printf '# Reviewer Report\n\nverdict: pass\n' > "$SMOKE_PLAN_DIR/reviewer_report.md"
  output="$(python3 "$REPO_ROOT/hermes.py" plan-status "$SMOKE_PLAN_ID")"
  printf '%s\n' "$output"
  assert_output_contains "$output" "verdict: pass"
  assert_output_contains "$output" "status: non_blocking"
  assert_output_contains "$output" "stop_signal: no"
  assert_output_contains "$output" "reviewer verdict does not block the plan"

  printf '# Reviewer Report\n\nverdict: mystery\n' > "$SMOKE_PLAN_DIR/reviewer_report.md"
  output="$(python3 "$REPO_ROOT/hermes.py" plan-status "$SMOKE_PLAN_ID")"
  printf '%s\n' "$output"
  assert_output_contains "$output" "verdict: mystery"
  assert_output_contains "$output" "status: unknown_verdict"

  printf '# Reviewer Report\n\n' > "$SMOKE_PLAN_DIR/reviewer_report.md"
  output="$(python3 "$REPO_ROOT/hermes.py" plan-status "$SMOKE_PLAN_ID")"
  printf '%s\n' "$output"
  assert_output_contains "$output" "verdict: missing"
  assert_output_contains "$output" "status: missing_verdict"

  printf '# Reviewer Report\n\nverdict: pass\n' > "$SMOKE_PLAN_DIR/reviewer_report.md"

  cat > "$SMOKE_PLAN_DIR/queue.md" <<'EOF'
Queue notes before the table should be ignored.

| id | title | status | dependencies | notes |
| --- | --- | --- | --- | --- |
| unit-001 | Completed base | completed | - | Done |
| unit-002 | Runnable pending | pending | unit-001 | Should be selected |
| unit-003 | Blocked pending | pending | unit-999 | Missing dependency |
| unit-004 | Needs work unit | needs_work | unit-001 | Needs work note |
| unit-005 | Unknown unit | unknown_status | - | Unknown note |

Trailing notes after the table should be ignored.
EOF

  output="$(python3 "$REPO_ROOT/hermes.py" plan-status "$SMOKE_PLAN_ID")"
  printf '%s\n' "$output"
  assert_output_contains "$output" "queue_counts:"
  assert_output_contains "$output" "pending"
  assert_output_contains "$output" "completed"
  assert_output_contains "$output" "needs_work"
  assert_output_contains "$output" "unknown"
  assert_output_contains "$output" "warnings"

  output="$(python3 "$REPO_ROOT/hermes.py" run-next "$SMOKE_PLAN_ID" --dry-run)"
  printf '%s\n' "$output"
  assert_output_contains "$output" "mode: dry-run"
  assert_output_contains "$output" "selected_unit: unit-002"
  assert_output_contains "$output" "blocked_units"
  assert_output_contains "$output" "unit-003"
  assert_output_contains "$output" "dependency_missing:unit-999"

  assert_repo_hermes_status_clean

  echo "Hermes v0.2-D reviewer report smoke test passed"
}

main "$@"
