#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

SMOKE_PLAN_ID="smoke-plan-status-state-validation"
HERMES_ROOT="$REPO_ROOT/.hermes"
SMOKE_PLAN_DIR="$HERMES_ROOT/plans/$SMOKE_PLAN_ID"
SMOKE_STATE_FILE="$SMOKE_PLAN_DIR/state.json"

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

cleanup() {
  safe_remove_smoke_plan "$SMOKE_PLAN_DIR"
}
trap cleanup EXIT

expect_contains() {
  local haystack="$1"; shift
  local needle="$1"; shift
  local label="$1"; shift
  if ! printf '%s' "$haystack" | grep -Fq -- "$needle"; then
    echo "FAIL: $label: expected output to contain: $needle" >&2
    echo "--- output ---" >&2
    echo "$haystack" >&2
    echo "--- end ---" >&2
    exit 1
  fi
}

expect_plan_status_zero() {
  local label="$1"
  local out
  set +e
  out="$(python3 "$REPO_ROOT/hermes.py" plan-status "$SMOKE_PLAN_ID" 2>&1)"
  local rc=$?
  set -e
  if [[ "$rc" -ne 0 ]]; then
    echo "FAIL: $label: expected plan-status exit 0, got $rc" >&2
    echo "--- output ---" >&2
    echo "$out" >&2
    echo "--- end ---" >&2
    exit 1
  fi
  printf '%s\n' "$out"
}

main() {
  cd "$REPO_ROOT"

  safe_remove_smoke_plan "$SMOKE_PLAN_DIR"

  python3 -m py_compile hermes.py
  python3 hermes.py plan-init "$SMOKE_PLAN_ID" \
    --title "Smoke Plan Status State Validation" \
    --objective "Verify plan-status state validation summary"

  rm -f -- "$SMOKE_STATE_FILE"

  local out
  out="$(expect_plan_status_zero "missing state file")"
  expect_contains "$out" "state_validation: not_found" "missing state not_found line"
  if [[ -e "$SMOKE_STATE_FILE" ]]; then
    echo "FAIL: plan-status must not create state.json when it is missing" >&2
    exit 1
  fi

  cat > "$SMOKE_STATE_FILE" <<'EOF'
{
  "schema_version": 1,
  "plan_id": "smoke-plan-status-state-validation",
  "state": "draft",
  "previous_state": null,
  "updated_at": "2026-05-15T10:00:00+09:00",
  "updated_by": "operator",
  "transition_reason": "valid smoke state",
  "history": []
}
EOF
  out="$(expect_plan_status_zero "valid state file")"
  expect_contains "$out" "state_validation: pass" "valid state pass line"
  expect_contains "$out" "state_validation_errors: 0" "valid state zero errors"
  expect_contains "$out" "state_validation_warnings: 0" "valid state zero warnings"

  cat > "$SMOKE_STATE_FILE" <<'EOF'
{
  "schema_version": 1,
  "plan_id": "smoke-plan-status-state-validation",
  "state": "paused",
  "previous_state": "draft",
  "updated_at": "2026-05-15T10:00:00+09:00",
  "updated_by": "operator",
  "transition_reason": "unknown state smoke",
  "history": []
}
EOF
  out="$(expect_plan_status_zero "unknown state file")"
  expect_contains "$out" "state_validation: fail" "unknown state fail line"
  expect_contains "$out" "state_validation_errors:" "unknown state error count line"

  printf '{ invalid json\n' > "$SMOKE_STATE_FILE"
  out="$(expect_plan_status_zero "invalid JSON state file")"
  expect_contains "$out" "state_validation: error" "invalid JSON error line"
  expect_contains "$out" "state_validation_errors: 1" "invalid JSON error count"
  expect_contains "$out" "state_validation_warnings: 0" "invalid JSON warning count"

  safe_remove_smoke_plan "$SMOKE_PLAN_DIR"

  bash "$REPO_ROOT/scripts/smoke_v0_2_c_run_next_dry_run.sh"
  bash "$REPO_ROOT/scripts/smoke_v0_3_e_validate_state.sh"

  echo "Hermes v0.3-H plan-status state validation smoke test passed"
}

main "$@"
