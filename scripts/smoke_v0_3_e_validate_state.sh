#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

TMP_ROOT="$(mktemp -d -t hermes-v0-3-e-XXXXXX)"
PLAN_ID="smoke-validate-state"

cleanup() {
  if [[ -n "${TMP_ROOT:-}" && -d "$TMP_ROOT" ]]; then
    rm -rf -- "$TMP_ROOT"
  fi
}
trap cleanup EXIT

write_state() {
  local path="$1"
  local body="$2"
  printf '%s' "$body" > "$path"
}

expect_exit() {
  local expected="$1"; shift
  local label="$1"; shift
  local out
  set +e
  out=$("$@" 2>&1)
  local rc=$?
  set -e
  if [[ "$rc" -ne "$expected" ]]; then
    echo "FAIL: $label: expected exit $expected, got $rc" >&2
    echo "--- output ---" >&2
    echo "$out" >&2
    echo "--- end ---" >&2
    exit 1
  fi
  printf '%s\n' "$out"
}

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

assert_no_tracked_changes() {
  local status
  status="$(git -C "$REPO_ROOT" status --short --untracked-files=no)"
  if [[ -n "$status" ]]; then
    echo "FAIL: expected clean tracked git status" >&2
    echo "$status" >&2
    exit 1
  fi
}

run_validate() {
  python3 "$REPO_ROOT/hermes.py" validate-state "$PLAN_ID" --state-file "$1"
}

main() {
  cd "$REPO_ROOT"

  python3 -m py_compile hermes.py

  local case_path

  # Case 1: valid minimal draft state -> pass exit 0
  case_path="$TMP_ROOT/valid_draft.json"
  write_state "$case_path" '{
    "schema_version": 1,
    "plan_id": "smoke-validate-state",
    "state": "draft",
    "previous_state": null,
    "updated_at": "2026-05-15T10:00:00+09:00",
    "updated_by": "operator",
    "transition_reason": "initial scaffold",
    "history": []
  }'
  out=$(expect_exit 0 "valid draft" run_validate "$case_path")
  expect_contains "$out" "state_validation: pass" "valid draft pass line"
  expect_contains "$out" "errors: 0" "valid draft zero errors"
  expect_contains "$out" "warnings: 0" "valid draft zero warnings"

  # Case 2: missing required field (no transition_reason) -> fail exit 1
  case_path="$TMP_ROOT/missing_field.json"
  write_state "$case_path" '{
    "schema_version": 1,
    "plan_id": "smoke-validate-state",
    "state": "draft",
    "previous_state": null,
    "updated_at": "2026-05-15T10:00:00+09:00",
    "updated_by": "operator",
    "history": []
  }'
  out=$(expect_exit 1 "missing required field" run_validate "$case_path")
  expect_contains "$out" "state_validation: fail" "missing field fail line"
  expect_contains "$out" "missing_required_field" "missing field reason"
  expect_contains "$out" "transition_reason" "missing field name"

  # Case 3: unknown state value -> fail exit 1
  case_path="$TMP_ROOT/unknown_state.json"
  write_state "$case_path" '{
    "schema_version": 1,
    "plan_id": "smoke-validate-state",
    "state": "paused",
    "previous_state": "draft",
    "updated_at": "2026-05-15T10:00:00+09:00",
    "updated_by": "operator",
    "transition_reason": "typo",
    "history": []
  }'
  out=$(expect_exit 1 "unknown state" run_validate "$case_path")
  expect_contains "$out" "unknown_state" "unknown state reason"
  expect_contains "$out" "value=paused" "unknown state value"

  # Case 4: invalid transition (queued -> completed) -> fail exit 1
  case_path="$TMP_ROOT/invalid_transition.json"
  write_state "$case_path" '{
    "schema_version": 1,
    "plan_id": "smoke-validate-state",
    "state": "completed",
    "previous_state": "queued",
    "updated_at": "2026-05-15T10:00:00+09:00",
    "updated_by": "operator",
    "transition_reason": "skipping ahead",
    "history": []
  }'
  out=$(expect_exit 1 "invalid transition" run_validate "$case_path")
  expect_contains "$out" "invalid_transition" "invalid transition reason"
  expect_contains "$out" "queued->completed" "invalid transition pair"

  # Case 5: blocked_by_reviewer -> running -> fail exit 1
  case_path="$TMP_ROOT/blocked_to_running.json"
  write_state "$case_path" '{
    "schema_version": 1,
    "plan_id": "smoke-validate-state",
    "state": "running",
    "previous_state": "blocked_by_reviewer",
    "updated_at": "2026-05-15T10:00:00+09:00",
    "updated_by": "operator",
    "transition_reason": "forced run",
    "history": []
  }'
  out=$(expect_exit 1 "blocked_by_reviewer to running" run_validate "$case_path")
  expect_contains "$out" "forbidden_transition" "blocked->running forbidden"
  expect_contains "$out" "blocked_by_reviewer->running" "blocked->running pair"

  # Case 6: archived -> running -> fail exit 1
  case_path="$TMP_ROOT/archived_to_running.json"
  write_state "$case_path" '{
    "schema_version": 1,
    "plan_id": "smoke-validate-state",
    "state": "running",
    "previous_state": "archived",
    "updated_at": "2026-05-15T10:00:00+09:00",
    "updated_by": "operator",
    "transition_reason": "resurrect",
    "history": []
  }'
  out=$(expect_exit 1 "archived to running" run_validate "$case_path")
  expect_contains "$out" "forbidden_transition" "archived->running forbidden"
  expect_contains "$out" "archived->running" "archived->running pair"

  # Case 7: malformed updated_at -> fail exit 1 (documented policy: fail)
  case_path="$TMP_ROOT/bad_updated_at.json"
  write_state "$case_path" '{
    "schema_version": 1,
    "plan_id": "smoke-validate-state",
    "state": "draft",
    "previous_state": null,
    "updated_at": "yesterday",
    "updated_by": "operator",
    "transition_reason": "initial scaffold",
    "history": []
  }'
  out=$(expect_exit 1 "malformed updated_at" run_validate "$case_path")
  expect_contains "$out" "invalid_iso8601" "malformed updated_at reason"

  # Case 8: history not a list -> fail exit 1
  case_path="$TMP_ROOT/history_not_list.json"
  write_state "$case_path" '{
    "schema_version": 1,
    "plan_id": "smoke-validate-state",
    "state": "draft",
    "previous_state": null,
    "updated_at": "2026-05-15T10:00:00+09:00",
    "updated_by": "operator",
    "transition_reason": "initial scaffold",
    "history": {}
  }'
  out=$(expect_exit 1 "history not list" run_validate "$case_path")
  expect_contains "$out" "field=history" "history field cited"
  expect_contains "$out" "invalid_type" "history not list reason"

  # Case 9a: review_gate_snapshot == unknown -> warn, exit 0 (documented policy)
  case_path="$TMP_ROOT/review_gate_unknown.json"
  write_state "$case_path" '{
    "schema_version": 1,
    "plan_id": "smoke-validate-state",
    "state": "awaiting_review",
    "previous_state": "dry_run_ready",
    "updated_at": "2026-05-15T10:00:00+09:00",
    "updated_by": "operator",
    "transition_reason": "queued for review",
    "history": [],
    "review_gate_snapshot": "unknown"
  }'
  out=$(expect_exit 0 "review_gate unknown warns" run_validate "$case_path")
  expect_contains "$out" "state_validation: pass" "review_gate unknown still pass"
  expect_contains "$out" "warning:" "review_gate unknown warning emitted"
  expect_contains "$out" "operator_review_required" "review_gate unknown warning reason"

  # Case 9b: review_gate_snapshot unrecognized string -> fail exit 1
  case_path="$TMP_ROOT/review_gate_bogus.json"
  write_state "$case_path" '{
    "schema_version": 1,
    "plan_id": "smoke-validate-state",
    "state": "awaiting_review",
    "previous_state": "dry_run_ready",
    "updated_at": "2026-05-15T10:00:00+09:00",
    "updated_by": "operator",
    "transition_reason": "queued for review",
    "history": [],
    "review_gate_snapshot": "definitely_approved"
  }'
  out=$(expect_exit 1 "review_gate unknown value" run_validate "$case_path")
  expect_contains "$out" "unknown_review_gate" "unknown review_gate reason"

  # Case 9c: review_gate_snapshot == blocked_by_reviewer with state running -> fail
  case_path="$TMP_ROOT/review_gate_blocking.json"
  write_state "$case_path" '{
    "schema_version": 1,
    "plan_id": "smoke-validate-state",
    "state": "running",
    "previous_state": "approved_for_manual_run",
    "updated_at": "2026-05-15T10:00:00+09:00",
    "updated_by": "operator",
    "transition_reason": "manual run",
    "history": [],
    "review_gate_snapshot": "blocked_by_reviewer"
  }'
  out=$(expect_exit 1 "review_gate blocked vs running" run_validate "$case_path")
  expect_contains "$out" "reviewer_blocked" "reviewer_blocked reason"

  # Case 10: missing state file -> exit 2
  expect_exit 2 "missing state file" \
    python3 "$REPO_ROOT/hermes.py" validate-state "$PLAN_ID" \
      --state-file "$TMP_ROOT/does_not_exist.json" >/dev/null

  # Case 11: invalid JSON -> exit 2
  case_path="$TMP_ROOT/not_json.json"
  printf '%s' '{ not valid json' > "$case_path"
  expect_exit 2 "invalid JSON" run_validate "$case_path" >/dev/null

  # Case 12: plan_id mismatch -> fail exit 1
  case_path="$TMP_ROOT/plan_mismatch.json"
  write_state "$case_path" '{
    "schema_version": 1,
    "plan_id": "other-plan",
    "state": "draft",
    "previous_state": null,
    "updated_at": "2026-05-15T10:00:00+09:00",
    "updated_by": "operator",
    "transition_reason": "initial scaffold",
    "history": []
  }'
  out=$(expect_exit 1 "plan_id mismatch" run_validate "$case_path")
  expect_contains "$out" "plan_id_mismatch" "plan_id_mismatch reason"

  # Case 13: validate-state from outside the repo must not create cwd files.
  local outside_cwd
  outside_cwd="$(mktemp -d -p "$TMP_ROOT" outside-cwd-XXXXXX)"
  out=$(expect_exit 0 "outside cwd read-only" \
    env -C "$outside_cwd" python3 "$REPO_ROOT/hermes.py" validate-state "$PLAN_ID" \
      --state-file "$TMP_ROOT/valid_draft.json")
  expect_contains "$out" "state_validation: pass" "outside cwd pass line"
  if [[ -e "$outside_cwd/IMPROVEMENTS.md" ]]; then
    echo "FAIL: validate-state must not create IMPROVEMENTS.md in cwd" >&2
    exit 1
  fi
  assert_no_tracked_changes

  # Safety: confirm validator did not create/modify .hermes/ for this smoke plan
  if [[ -e "$REPO_ROOT/.hermes/plans/$PLAN_ID" ]]; then
    echo "FAIL: validator must not touch .hermes/plans/$PLAN_ID" >&2
    exit 1
  fi

  echo "Hermes v0.3-E validate-state smoke test passed"
}

main "$@"
