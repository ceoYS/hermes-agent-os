#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

SMOKE_ROOT="$(mktemp -d /tmp/hermes-v02e-smoke.XXXXXX)"
SMOKE_PLAN_ID="smoke-review-gate"
SMOKE_PLAN_DIR="$SMOKE_ROOT/.hermes/plans/$SMOKE_PLAN_ID"

cleanup() {
  case "$SMOKE_ROOT" in
    /tmp/hermes-v02e-smoke.*) rm -rf -- "$SMOKE_ROOT" ;;
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

assert_output_not_contains() {
  local output="$1"
  local needle="$2"
  if grep -Fq -- "$needle" <<<"$output"; then
    echo "expected output not to contain: $needle" >&2
    exit 1
  fi
}

write_plan_fingerprints() {
  local output_path="$1"
  local file
  : > "$output_path"
  for file in plan.md queue.md state.json log.md morning_brief.md reviewer_report.md; do
    assert_file_exists "$SMOKE_PLAN_DIR/$file"
    cksum "$SMOKE_PLAN_DIR/$file" >> "$output_path"
  done
}

assert_fingerprints_equal() {
  local before="$1"
  local after="$2"
  if ! diff -u "$before" "$after"; then
    echo "expected run-next --dry-run not to mutate plan files" >&2
    exit 1
  fi
}

main() {
  trap cleanup EXIT
  cd "$SMOKE_ROOT"

  run python3 -m py_compile "$REPO_ROOT/hermes.py"
  run python3 "$REPO_ROOT/hermes.py" plan-init "$SMOKE_PLAN_ID" \
    --title "Smoke Review Gate" \
    --objective "Verify reviewer gate status summary"

  local output
  output="$(python3 "$REPO_ROOT/hermes.py" plan-status "$SMOKE_PLAN_ID")"
  printf '%s\n' "$output"
  assert_output_contains "$output" "verdict: pending"
  assert_output_contains "$output" "review_gate: open"

  printf '# Reviewer Report\n\nverdict: needs_work\n' > "$SMOKE_PLAN_DIR/reviewer_report.md"
  output="$(python3 "$REPO_ROOT/hermes.py" plan-status "$SMOKE_PLAN_ID")"
  printf '%s\n' "$output"
  assert_output_contains "$output" "verdict: needs_work"
  assert_output_contains "$output" "review_gate: blocked_by_reviewer"

  printf '# Reviewer Report\n\nverdict: blocked\n' > "$SMOKE_PLAN_DIR/reviewer_report.md"
  output="$(python3 "$REPO_ROOT/hermes.py" plan-status "$SMOKE_PLAN_ID")"
  printf '%s\n' "$output"
  assert_output_contains "$output" "verdict: blocked"
  assert_output_contains "$output" "review_gate: blocked_by_reviewer"

  printf '# Reviewer Report\n\nverdict: pass\n' > "$SMOKE_PLAN_DIR/reviewer_report.md"
  output="$(python3 "$REPO_ROOT/hermes.py" plan-status "$SMOKE_PLAN_ID")"
  printf '%s\n' "$output"
  assert_output_contains "$output" "verdict: pass"
  assert_output_contains "$output" "review_gate: open"
  assert_output_not_contains "$output" "review_gate: blocked_by_reviewer"

  printf '# Reviewer Report\n\nverdict: pass_with_notes\n' > "$SMOKE_PLAN_DIR/reviewer_report.md"
  output="$(python3 "$REPO_ROOT/hermes.py" plan-status "$SMOKE_PLAN_ID")"
  printf '%s\n' "$output"
  assert_output_contains "$output" "verdict: pass_with_notes"
  assert_output_contains "$output" "review_gate: open"
  assert_output_not_contains "$output" "review_gate: blocked_by_reviewer"

  printf '# Reviewer Report\n\nverdict: mystery\n' > "$SMOKE_PLAN_DIR/reviewer_report.md"
  output="$(python3 "$REPO_ROOT/hermes.py" plan-status "$SMOKE_PLAN_ID")"
  printf '%s\n' "$output"
  assert_output_contains "$output" "verdict: mystery"
  assert_output_contains "$output" "status: unknown_verdict"
  assert_output_contains "$output" "review_gate: unknown"

  printf '# Reviewer Report\n\n' > "$SMOKE_PLAN_DIR/reviewer_report.md"
  output="$(python3 "$REPO_ROOT/hermes.py" plan-status "$SMOKE_PLAN_ID")"
  printf '%s\n' "$output"
  assert_output_contains "$output" "verdict: missing"
  assert_output_contains "$output" "status: missing_verdict"
  assert_output_contains "$output" "review_gate: unknown"

  printf '# Reviewer Report\n\nverdict: pass_with_notes\n' > "$SMOKE_PLAN_DIR/reviewer_report.md"
  cat > "$SMOKE_PLAN_DIR/queue.md" <<'EOF'
| id | title | status | dependencies | notes |
| --- | --- | --- | --- | --- |
| unit-001 | Completed base | completed | - | Done |
| unit-002 | Runnable pending | pending | unit-001 | Should be selected |
| unit-003 | Blocked pending | pending | unit-999 | Missing dependency |
EOF

  local before_fingerprints="$SMOKE_ROOT/before.cksum"
  local after_fingerprints="$SMOKE_ROOT/after.cksum"
  write_plan_fingerprints "$before_fingerprints"

  output="$(python3 "$REPO_ROOT/hermes.py" run-next "$SMOKE_PLAN_ID" --dry-run)"
  printf '%s\n' "$output"
  assert_output_contains "$output" "mode: dry-run"
  assert_output_contains "$output" "selected_unit: unit-002"
  assert_output_contains "$output" "dependency_missing:unit-999"

  write_plan_fingerprints "$after_fingerprints"
  assert_fingerprints_equal "$before_fingerprints" "$after_fingerprints"

  echo "Hermes v0.2-E review gate smoke test passed"
}

main "$@"
