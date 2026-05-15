#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

SMOKE_PLAN_ID="smoke-plan"
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

assert_file_exists() {
  local path="$1"
  if [[ ! -f "$path" ]]; then
    echo "expected file to exist: $path" >&2
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

main() {
  cd "$REPO_ROOT"

  safe_remove_smoke_plan "$SMOKE_PLAN_DIR"

  run python3 -m py_compile hermes.py
  run python3 hermes.py --help
  run python3 hermes.py plan-init "$SMOKE_PLAN_ID" --title "Smoke Plan" --objective "Verify plan scaffold"
  run python3 hermes.py plan-status "$SMOKE_PLAN_ID"

  assert_file_exists "$HERMES_ROOT/inbox.md"
  assert_file_exists "$SMOKE_PLAN_DIR/plan.md"
  assert_file_exists "$SMOKE_PLAN_DIR/queue.md"
  assert_file_exists "$SMOKE_PLAN_DIR/log.md"
  assert_file_exists "$SMOKE_PLAN_DIR/state.json"
  assert_file_exists "$SMOKE_PLAN_DIR/morning_brief.md"
  assert_file_exists "$SMOKE_PLAN_DIR/reviewer_report.md"
  assert_contains "$SMOKE_PLAN_DIR/state.json" '"plan_id": "smoke-plan"'

  safe_remove_smoke_plan "$SMOKE_PLAN_DIR"

  echo "Hermes v0.2-A plan scaffold smoke test passed"
}

main "$@"
