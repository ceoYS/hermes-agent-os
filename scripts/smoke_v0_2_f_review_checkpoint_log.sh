#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

SMOKE_ROOT="$(mktemp -d /tmp/hermes-v02f-smoke.XXXXXX)"
SMOKE_PLAN_ID="smoke-review-checkpoint-log"
SMOKE_PLAN_DIR="$SMOKE_ROOT/.hermes/plans/$SMOKE_PLAN_ID"

cleanup() {
  case "$SMOKE_ROOT" in
    /tmp/hermes-v02f-smoke.*) rm -rf -- "$SMOKE_ROOT" ;;
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

assert_dir_exists() {
  local path="$1"
  if [[ ! -d "$path" ]]; then
    echo "expected directory to exist: $path" >&2
    exit 1
  fi
}

assert_contains() {
  local path="$1"
  local needle="$2"
  if ! grep -Fq -- "$needle" "$path"; then
    echo "expected $path to contain: $needle" >&2
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
  run python3 "$REPO_ROOT/hermes.py" plan-init "$SMOKE_PLAN_ID" \
    --title "Smoke Review Checkpoint Log" \
    --objective "Verify manual review checkpoint log scaffold"

  assert_dir_exists "$SMOKE_PLAN_DIR"
  assert_file_exists "$SMOKE_PLAN_DIR/log.md"
  assert_contains "$SMOKE_PLAN_DIR/log.md" "## Manual Review Checkpoints"
  assert_contains "$SMOKE_PLAN_DIR/log.md" "| timestamp | reviewer | checkpoint | verdict | notes |"
  assert_contains "$SMOKE_PLAN_DIR/log.md" "pending"
  assert_contains "$SMOKE_PLAN_DIR/log.md" "pass"
  assert_contains "$SMOKE_PLAN_DIR/log.md" "pass_with_notes"
  assert_contains "$SMOKE_PLAN_DIR/log.md" "needs_work"
  assert_contains "$SMOKE_PLAN_DIR/log.md" "blocked"
  assert_contains "$SMOKE_PLAN_DIR/log.md" "human-maintained audit log"
  assert_contains "$SMOKE_PLAN_DIR/log.md" "not an automatic source of truth"

  local output
  output="$(python3 "$REPO_ROOT/hermes.py" plan-status "$SMOKE_PLAN_ID")"
  printf '%s\n' "$output"
  assert_output_contains "$output" "plan_id: $SMOKE_PLAN_ID"
  assert_output_contains "$output" "status: created"
  assert_output_contains "$output" "review_gate: open"

  assert_repo_hermes_status_clean

  echo "Hermes v0.2-F review checkpoint log smoke test passed"
}

main "$@"
